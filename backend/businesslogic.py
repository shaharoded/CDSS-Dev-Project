"""
Business Logic Layer for CDSS Project.

Handles all patient-related operations by combining
SQL queries and data access functions.

All SQL queries are saved separately under /queries/
"""
import pandas as pd
import re

# Local Code
from backend.dataaccess import DataAccess
from backend.backend_config import *  # all query paths

data = DataAccess()

## ------------------ Validation Functions ------------------
def validate_patient_id(patient_id):
    if not patient_id.isdigit():
        raise ValueError("Patient ID must contain digits only.")
    if len(patient_id) != 9:
        raise ValueError("Patient ID must be exactly 9 digits long.")

def validate_name(name, field_name):
    """
    Allows alphabetic names with optional hyphens or apostrophes.
    """
    pattern = r"^[A-Za-z'-]+$"
    if not re.fullmatch(pattern, name):
        raise ValueError(f"{field_name} must contain only letters, hyphens (-), or apostrophes (').")

def validate_datetime(dt_string):
    try:
        dt = pd.to_datetime(dt_string, dayfirst=True)
        return dt
    except Exception:
            raise ValueError(f"Invalid date input: '{dt_string}' could not be parsed as a date or datetime.")

def validate_dates_relation(early_date, later_date, early_field_name, later_field_name):
    if early_date and later_date:
        early_dt = validate_datetime(early_date)
        later_dt = validate_datetime(later_date)
        if later_dt < early_dt:
            raise ValueError(f"{later_field_name} cannot be earlier than {early_field_name}.")

# ------------------ Class Exceptions ------------------
class PatientNotFound(Exception):
    """Raised when patient is not found in DB."""
    pass

class LoincCodeNotFound(Exception):
    """Raised when a Loinc code is not found in DB."""
    pass

class RecordNotFound(Exception):
    """Raised when a measurement record for a patient is not found in DB."""
    pass



class PatientRecord:
    """
    Main patient record class to handle business logic.
    Allows for empty initialization, As input will be given by the UI.
    """
    def __init__(self, patient_id=None, first_name=None, last_name=None):
        self.patient_id = patient_id
        self.first_name = first_name
        self.last_name = last_name
    
    @staticmethod
    def get_patient_by_name(first_name, last_name):
        """
        Returns the list of matching patients by their names.
        """
        # Input cleanup
        first_name, last_name = str(first_name).strip(), str(last_name).strip()
        # Check if Patient Name exists (without name check)
        matches = data.fetch_records(CHECK_PATIENT_BY_NAME_QUERY, (first_name, last_name))
        if not matches:
           raise PatientNotFound("Patient not found")
         
        return matches  # Return ID, First Name, Last Name from DB for every matching patient by name

    @staticmethod
    def search_history(patient_id, snapshot_date=None, loinc_num=None, start=None, end=None):
        """
        Search patient measurement history using optional filters:
        - snapshot_date: point-in-time view of the database.
        - loinc_num: filter by LOINC code.
        - start/end: define a datetime window (inclusive).
        Accepts both date and datetime; if only date is given, assumes 00:00 for start and 23:59 for end.

        NOTE: SEARCH_HISTORY_QUERY performs a JOIN with the LOINC table.
        """
        # Input cleanup
        for param in [patient_id, snapshot_date, loinc_num, start, end]:
            if param:
                param = str(param).strip()

        # Input validation
        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")
        validate_dates_relation(start, end, 'Start Date', 'End Date')
        validate_dates_relation(end, snapshot_date, 'End Date', 'Snapshot Date')

        # Initialize dynamic filters
        filters = ["m.PatientId = ?"]
        params = [patient_id]

        if loinc_num:
            filters.append("m.LoincNum = ?")
            params.append(loinc_num)

        # Handle datetime range
        if start:
            start_iso = validate_datetime(start) # 00:00:00 if no time, actual time if present
            filters.append("m.ValidStartTime >= ?")
            params.append(start_iso.strftime('%Y-%m-%d %H:%M:%S'))

        if end:
            if len(end.strip()) <= 10:  # format like 'YYYY-MM-DD' -> No time
                end_dt = validate_datetime(end)
                end_iso = end_dt.replace(hour=23, minute=59, second=59)
            else:
                end_dt = validate_datetime(end)
                end_iso = end_dt
            filters.append("m.ValidStartTime <= ?")
            params.append(end_iso.strftime('%Y-%m-%d %H:%M:%S'))

        # Snapshot logic
        if snapshot_date:
            # Convert to ISO format
            snapshot_date = validate_datetime(snapshot_date)
            snapshot_iso = snapshot_date.strftime('%Y-%m-%d %H:%M:%S')
            filters.append("m.TransactionInsertionTime <= ?")
            filters.append("(m.TransactionDeletionTime IS NULL OR m.TransactionDeletionTime > ?)")
            params.extend([snapshot_iso, snapshot_iso])
        else:
            # Default to currently active records
            filters.append("(m.TransactionDeletionTime IS NULL OR m.TransactionDeletionTime > CURRENT_TIMESTAMP)")

        where_clause = " AND ".join(filters)

        # Read base query from file and insert where clause
        with open(SEARCH_HISTORY_QUERY, 'r') as f:
            base_query = f.read()

        final_query = base_query.replace("{where_clause}", where_clause)
        result = data.fetch_records(final_query, params)
        return result
   
    @staticmethod
    def register_patient(patient_id, first_name, last_name):
        """
        Inserts a patient to the DB.
        """
        # Input cleanup
        patient_id = str(patient_id).strip()
        first_name = str(first_name).strip()
        last_name = str(last_name).strip()
        
        # Validations:
        if data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise ValueError("You tried to input an existing patient into the system.\nUse the search tab to verify your input.")
        validate_patient_id(patient_id)
        validate_name(first_name, 'First Name')
        validate_name(last_name, 'Last Name')
        
        # Insert new patient
        data.execute_query(INSERT_PATIENT_QUERY, (patient_id, first_name, last_name))
    
    @staticmethod
    def insert_measurement(patient_id, valid_start_time, value, unit, component=None, loinc_num=None, transaction_time=None):
        """
        Insert a new measurement for a patient.

        - Using existing validation methods before inserting the new record.
        - Insert measurement using INSERT_MEASUREMENT_QUERY.
        - Raise PatientNotFound and LoincCodeNotFound if not exists, or ValueError is the dates are not in a parseable format
        - Will not allow user to insert an unupdated version of an existing record into the system.
        """
        # Input cleanup
        patient_id = str(patient_id).strip()
        loinc_num = str(loinc_num).strip()
        value = str(value).strip()
        unit = str(unit).strip()
        valid_start_time = str(valid_start_time).strip()
        transaction_time = str(transaction_time).strip() if transaction_time else transaction_time

        # Verify input
        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")
        
        # CASE 1: Both LOINC and Component provided → check match
        if loinc_num and component:
            loinc_num_1 = loinc_num
            loinc_num_2 = str(data.get_attr(GET_LOINC_BY_COMPONENT_QUERY, (component,))).strip()
            if not loinc_num_1 == loinc_num_2:
                raise ValueError(f"LOINC code '{loinc_num_1}' and component '{component}' do not match. The input component returned Loinc-Code={loinc_num_2}. Check the LOINC repository to fetch the correct code / name of the intended concept.")
        
        # CASE 2: Only Component provided → look up LOINC code
        elif component and not loinc_num:
            loinc_num = data.get_attr(GET_LOINC_BY_COMPONENT_QUERY, (component,))
            if not loinc_num:
                raise ValueError(f"No LOINC code found for component '{component}' in LOINC table. Check the LOINC repository to fetch the correct code / name of the intended concept.")
        
        # CASE 3: Only LOINC-Code provided → continue as usual
        elif loinc_num:
            if not data.check_record(CHECK_LOINC_QUERY, (loinc_num,)):
                raise LoincCodeNotFound("LOINC code not found in LOINC table.")
        else:
            raise ValueError("You must provide at least a LOINC code or a component name in order to update a measurement.")
        
        valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        transaction_time = validate_datetime(transaction_time).strftime('%Y-%m-%d %H:%M:%S')
        validate_dates_relation(valid_start_time, transaction_time, 'Valid Start Date', 'Transaction Insertion Time')

        # Check if this record already exists (and needs to be handled with update, not insert)
        if data.check_record(CHECK_RECORD_QUERY, (patient_id, loinc_num, valid_start_time, transaction_time)):
            raise ValueError("This record already exists in the DB and must be updated - not inserted. You cannot insert a new record with the same PatientId + LoincNum + ValidStartTime as another record.")

        # Insert measurement
        data.execute_query(
            INSERT_MEASUREMENT_QUERY,
            (patient_id, loinc_num, value, unit, valid_start_time, transaction_time)
        )

    @staticmethod
    def update_measurement(patient_id, valid_start_time, new_value,component=None, loinc_num=None, transaction_time=None):
        """
        Update an existing measurement value.

        - Use CHECK_PATIENT_QUERY to verify existence.
        - Update value using UPDATE_MEASUREMENT_QUERY.
        - Handle edge cases: no matching record.
        """
        # Input cleanup
        patient_id = str(patient_id).strip()
        loinc_num = str(loinc_num).strip()
        valid_start_time = str(valid_start_time).strip()
        new_value = str(new_value).strip()
        transaction_time = str(transaction_time).strip() if transaction_time else transaction_time
        
        # Verify input
        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")

        # CASE 1: Both LOINC and Component provided → check match
        if loinc_num and component:
            loinc_num_1 = loinc_num
            loinc_num_2 = str(data.get_attr(GET_LOINC_BY_COMPONENT_QUERY, (component,))).strip()
            if not loinc_num_1 == loinc_num_2:
                raise ValueError(f"LOINC code '{loinc_num_1}' and component '{component}' do not match. The input component returned Loinc-Code={loinc_num_2}. Check the LOINC repository to fetch the correct code / name of the intended concept.")
        
        # CASE 2: Only Component provided → look up LOINC code
        elif component and not loinc_num:
            loinc_num = data.get_attr(GET_LOINC_BY_COMPONENT_QUERY, (component,))
            if not loinc_num:
                raise ValueError(f"No LOINC code found for component '{component}' in LOINC table. Check the LOINC repository to fetch the correct code / name of the intended concept.")
        
        # CASE 3: Only LOINC-Code provided → continue as usual
        elif loinc_num:
            if not data.check_record(CHECK_LOINC_QUERY, (loinc_num,)):
                raise LoincCodeNotFound("LOINC code not found in LOINC table.")
        else:
            raise ValueError("You must provide at least a LOINC code or a component name in order to update a measurement.")

        valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        transaction_time = validate_datetime(transaction_time).strftime('%Y-%m-%d %H:%M:%S')
        validate_dates_relation(valid_start_time, transaction_time, 'Valid Start Date', 'Transaction Insertion Time')
        
        # Check if this record doesn't exists (and needs to be handled with insert, not update)
        if not data.check_record(CHECK_RECORD_QUERY, (patient_id, loinc_num, valid_start_time, transaction_time)):
            raise RecordNotFound("This record was not found in the DB. If this record should exist - maybe you used an irrelevant DB snapshot? (with Transaction time), else - please use the Insert Measurement tab")

        # In case transaction_time is not the most updated TransactionInsertionTime for this record, get the TransactionDeletionDate for it
        # deletion_date can be None
        future_record_date = data.get_attr(CHECK_FUTURE_RECORD_QUERY, (patient_id, loinc_num, valid_start_time, transaction_time))
        if future_record_date:
            raise ValueError(f"This record has a newer update from {future_record_date} and cannot be updated to an unupdated version.")
        
        # Fetch the unit from existing records
        unit = data.get_attr(GET_EXISTING_UNIT_QUERY, (patient_id, loinc_num, valid_start_time))
        # No exception in case non found, as that's the reflection of this concept in the DB.

        # Insert the new measurement row
        data.execute_query(
            INSERT_MEASUREMENT_QUERY,
            (patient_id, loinc_num, new_value, unit, valid_start_time, transaction_time)
        )

        # Update end time on older records
        data.execute_query(
            UPDATE_OLD_RECORDS_QUERY,
            (transaction_time, patient_id, loinc_num, valid_start_time, transaction_time, transaction_time)
        )

    @staticmethod
    def delete_measurement(patient_id, loinc_num=None, valid_start_time=None, deletion_time=None, component=None):
        """
        Logically deletes a measurement (sets TransactionDeletionTime).

        - Uses LOINC code or component name to identify the measurement.
        - Verifies that the record isn't already deleted.
        - Returns the record before deletion for confirmation.
        """
        # Input cleanup
        patient_id = str(patient_id).strip()
        valid_start_time = str(valid_start_time).strip()
        deletion_time = str(deletion_time).strip() if deletion_time else None

        # Validate patient
        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")

        if loinc_num and component:
            loinc_num_1 = loinc_num
            loinc_num_2 = str(data.get_attr(GET_LOINC_BY_COMPONENT_QUERY, (component,))).strip()
            if not loinc_num_1 == loinc_num_2:
                raise ValueError(f"LOINC code '{loinc_num_1}' and component '{component}' do not match. The input component returned Loinc-Code={loinc_num_2}. Check the LOINC repository to fetch the correct code / name of the intended concept.")

        # Resolve LOINC code if only component is given
        if not loinc_num and component:
            loinc_row = data.fetch_records(GET_LOINC_BY_COMPONENT_QUERY, (component,))
            if loinc_row:
                loinc_num = loinc_row[0][0]
            else:
                raise ValueError(f"No LOINC code found for component '{component}'")
        elif loinc_num:
            loinc_num = str(loinc_num).strip()
            if not data.check_record(CHECK_LOINC_QUERY, (loinc_num,)):
                raise LoincCodeNotFound("Loinc code not found")

        # If only a date was given, get the latest ValidStartTime on that date
        if len(valid_start_time) <= 10:
            date_only = validate_datetime(valid_start_time).strftime('%Y-%m-%d')
            with open(SELECT_LATEST_VALIDTIME_FOR_DAY_QUERY, 'r') as f:
                query = f.read()
            result = data.cur.execute(query, (patient_id, loinc_num, date_only)).fetchone()
            if not result:
                raise RecordNotFound(f"No measurement found on {date_only} for LOINC {loinc_num}")
            valid_start_time = result[0]
        else:
            valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')

        if deletion_time:
            deletion_time = validate_datetime(deletion_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            from datetime import datetime
            deletion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if record exists
        if not data.check_record(CHECK_RECORD_FOR_DELETION, (patient_id, loinc_num, valid_start_time)):
            raise RecordNotFound("This record was not found in the DB")

        # Check if already deleted
        with open(CHECK_IF_DELETED_QUERY, 'r') as f:
            check_query = f.read()
        existing = data.cur.execute(check_query, (patient_id, loinc_num, valid_start_time)).fetchone()
        if existing and existing[0] is not None:
            raise ValueError(f"This record was already deleted or scheduled to be deleted at {existing[0]}")

        # Perform logical deletion
        data.execute_query(
            UPDATE_RECORD_DELETION_TIME_QUERY,
            (deletion_time, patient_id, loinc_num, valid_start_time)
        )

        # Fetch row after deletion
        with open(SELECT_MEASUREMENT_BEFORE_DELETE_QUERY, 'r') as f:
            preview_query = f.read()
        row = data.cur.execute(preview_query, (patient_id, loinc_num, valid_start_time)).fetchone()

        return row




if __name__ == "__main__":
    import sys

    print("🔍 Running business logic tests...")

    record = PatientRecord()

    try:
        first_name, last_name = "Eyal", "Rothman"
        print("\n🧪 Test 1: Get patient by name (should succeed)...")
        result = record.get_patient_by_name(first_name, last_name)
        for r in result:
            print(f"✅ Found: ID={r[0]}, FirstName={r[1]}, LastName={r[2]}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        print("Testing raw fetch...")
        rows = data.fetch_records(CHECK_PATIENT_BY_NAME_QUERY, (first_name, last_name))
        print("Result from DB:", rows)
        if not rows:
            rows = data.fetch_records('SELECT * FROM Patients', ())
            print("All patients from DB:", rows)
        sys.exit(1)

    try:
        print("\n🧪 Test 2: Search history with snapshot and range...")
        history = record.search_history(
            patient_id="345678904",
            snapshot_date="01/01/2024 12:00",
            start="01/01/2000",
            end="02/01/2023"
        )
        print(f"✅ Found {len(history)} records")
        for row in history:
            print("   ", row)
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        sys.exit(1)

    # try:
    #     print("\n🧪 Test 3: Register a new patient (should succeed or fail if already exists)...")
    #     record.register_patient("208388918", "Shahar", "Oded")
    #     print("✅ Registered patient successfully")
    # except Exception as e:
    #     print(f"❌ Test 3 failed: {e}")
    #     sys.exit(1)

    # try:
    #     print("\n🧪 Test 4: Insert measurement (should validate and insert)...")
    #     record.insert_measurement(
    #         patient_id="123456789",
    #         loinc_num="718-7",
    #         value="14.2",
    #         unit="mmol/L",
    #         valid_start_time="01/04/2024 08:00",
    #         transaction_time="01/04/2024 08:01"
    #     )
    #     print("✅ Inserted measurement")
    # except Exception as e:
    #     print(f"❌ Test 4 failed: {e}")
    #     sys.exit(1)
    #
    # print("\n✅ All tests completed successfully!")

    # try:
    #     print("\n🧪 Test 5: Delete existing measurement (valid case)...")
    #     row = record.delete_measurement(
    #         patient_id="345678904",
    #         loinc_num="11218-5",
    #         valid_start_time="2018-05-17 13:11:00",
    #         deletion_time="2026/02/04 10:00:00"
    #     )
    #     print("✅ Deleted measurement:")
    #     print("   ", row)
    # except Exception as e:
    #     print(f"❌ Test 5 failed: {e}")

    # try:
    #     print("\n🧪 Test 6: Delete non-existing measurement (should fail)...")
    #     record.delete_measurement(
    #         patient_id="345678904",
    #         loinc_num="9999-9",
    #         valid_start_time="2018-05-17 16:00:00"
    #     )
    #     print("❌ Test 6 failed: deletion should have failed for non-existent record")
    # except RecordNotFound as e:
    #     print(f"✅ Correctly failed with RecordNotFound: {e}")
    # except Exception as e:
    #     print(f"❌ Test 6 failed with unexpected error: {e}")
    #
    # try:
    #     print("\n🧪 Test 7: Delete already deleted measurement (should fail)...")
    #     # Try deleting again the same record from test 5
    #     record.delete_measurement(
    #         patient_id="345678904",
    #         loinc_num="11218-5",
    #         valid_start_time="2018-05-17 13:11:00"
    #     )
    #     print("❌ Test 7 failed: deletion should have been blocked due to prior deletion")
    # except ValueError as e:
    #     print(f"✅ Correctly failed with ValueError (already deleted): {e}")
    # except Exception as e:
    #     print(f"❌ Test 7 failed with unexpected error: {e}")
    #
    try:
        print("\n🧪 Test 8: Delete by component name only (no LOINC given)...")
        row = record.delete_measurement(
            patient_id="345678904",
            component="Heart rate",
            valid_start_time="2018-05-17 16:15:00"
        )
        print("✅ Deleted measurement by component:")
        print("   ", row)
    except Exception as e:
        print(f"❌ Test 8 failed: {e}")
    #
    # try:
    #     print("\n🧪 Test 9: Delete by date only (without time)...")
    #     row = record.delete_measurement(
    #         patient_id="123456789",
    #         loinc_num="718-7",
    #         valid_start_time="03/04/2024"  # no time
    #     )
    #     print("✅ Deleted measurement using date only (latest on that date):")
    #     print("   ", row)
    # except Exception as e:
    #     print(f"❌ Test 9 failed: {e}")





