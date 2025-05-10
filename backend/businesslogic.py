"""
Business Logic Layer for CDSS Project.

Handles all patient-related operations by combining
SQL queries and data access functions.

All SQL queries are saved separately under /queries/

TO-DO / THINK (to manual):
- Update and delete currently suggest you the LOINC codes relevant for the person if you try action by LOINC name, 
    but it will refer to action by loinc code if name is not unique. Insert will do the same but for all of the LOINC table. 
- Currently there is no suggestion of loinc name when a substring is inserted. Not sure we can create something like this properly.
- During measure insersion we are not checking that the inserted record does not already exists and are not blocking insersions of the same loinc_num at the same time (probably better)
"""
import pandas as pd
import re
from datetime import datetime


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
    if dt_string is not None:
        try:
            # Match ISO formats like 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM', 'YYYY-MM-DD HH:MM:SS'
            if re.match(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$", dt_string):
                return pd.to_datetime(dt_string, dayfirst=False)
            else:
                return pd.to_datetime(dt_string, dayfirst=True)
        except Exception:
            raise ValueError(f"Invalid date input: '{dt_string}' could not be parsed as a date or datetime.")

def validate_dates_relation(early_date, later_date, early_field_name, later_field_name):
    if early_date is not None and later_date is not None:
        early_dt = validate_datetime(early_date) if isinstance(early_date, str) else early_date
        later_dt = validate_datetime(later_date) if isinstance(later_date, str) else later_date
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
        Uses to verify the patient's ID if only name is known and to solve duplications in the system.
        """
        # Verify input
        if not first_name:
            raise ValueError("You cannot search for a patient without their first name.")
        if not last_name:
            raise ValueError("You cannot search for a patient without their first name.")
        
        # Input cleanup
        first_name, last_name = str(first_name).strip(), str(last_name).strip()
        # Check if Patient Name exists (without name check)
        matches = data.fetch_records(CHECK_PATIENT_BY_NAME_QUERY, (first_name, last_name))
        if not matches:
           raise PatientNotFound("Patient not found")
         
        return matches  # Return ID, First Name, Last Name from DB for every matching patient by name

    @staticmethod
    def search_history(patient_id, snapshot_date=None, loinc_num=None, component=None, start=None, end=None):
        """
        Search patient measurement history using optional filters:
        - snapshot_date: point-in-time view of the database.
        - loinc_num: filter by LOINC code.
        - component: filter (LIKE condition) by loinc component name.
        - start/end: define a datetime window (inclusive).
        Accepts both date and datetime; if only date is given, assumes 00:00 for start and 23:59 for end.

        NOTE: SEARCH_HISTORY_QUERY performs a JOIN with the LOINC table.
        """
        # Verify input
        if not patient_id:
            raise ValueError("Patient ID must be provided and cannot be empty.")
        
        # Input cleanup
        patient_id = str(patient_id).strip()
        loinc_num = str(loinc_num).strip() if loinc_num else None
        component = str(component).strip() if component else None
        start = str(start).strip() if start else None
        end = str(end).strip() if end else None
        snapshot_date = str(snapshot_date).strip() if snapshot_date else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Input validation
        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")
        validate_dates_relation(start, end, 'Start Date', 'End Date')
        validate_dates_relation(start, snapshot_date, 'Start Date', 'Snapshot Date')
        validate_dates_relation(end, snapshot_date, 'End Date', 'Snapshot Date')

        # Initialize dynamic filters
        filters = ["m.PatientId = ?"]
        params = [patient_id]

        if loinc_num:
            filters.append("m.LoincNum = ?")
            params.append(loinc_num)
        
        if component:
            filters.append("LOWER(l.Component) LIKE '%' || LOWER(?) || '%'")
            params.append(component)

        # Handle datetime range
        if start:
            start_iso = validate_datetime(start) # 00:00:00 if no time, actual time if present
            filters.append("m.ValidStartTime >= ?")
            params.append(start_iso.strftime('%Y-%m-%d %H:%M:%S'))

        if end:
            if len(end) <= 10:  # format like 'YYYY-MM-DD' -> No time
                end_dt = validate_datetime(end)
                end_iso = end_dt.replace(hour=23, minute=59, second=59)
            else:
                end_iso = validate_datetime(end)
            filters.append("m.ValidStartTime <= ?")
            params.append(end_iso.strftime('%Y-%m-%d %H:%M:%S'))

        # Snapshot logic (always relevant)
        if isinstance(snapshot_date, str) and len(snapshot_date) <= 10: # format like 'YYYY-MM-DD' -> No time (only manual input)
            snapshot_date = validate_datetime(snapshot_date)
            snapshot_date = snapshot_date.replace(hour=23, minute=59, second=59)
        elif isinstance(snapshot_date, str):
            snapshot_date = validate_datetime(snapshot_date)
        # Else: No change needed, it's already a date-time.
            
        # Convert to ISO format and extend query
        snapshot_iso = snapshot_date.strftime('%Y-%m-%d %H:%M:%S')
        filters.append("m.TransactionInsertionTime <= ?")
        filters.append("(m.TransactionDeletionTime IS NULL OR m.TransactionDeletionTime > ?)")
        params.extend([snapshot_iso, snapshot_iso])

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
        Inserts a new patient to the DB (Patients table).
        """
        # Verify input
        if not patient_id:
            raise ValueError("Patient ID must be provided and cannot be empty.")
        if not first_name:
            raise ValueError("You cannot register a new patient without their first name.")
        if not last_name:
            raise ValueError("You cannot register a new patient without their first name.")
        
        # Input cleanup
        patient_id = str(patient_id).strip()
        first_name = str(first_name).strip().capitalize()
        last_name = str(last_name).strip().capitalize()
        
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
        # Verify input
        if not patient_id:
            raise ValueError("Patient ID must be provided and cannot be empty.")
        if not value:
            raise ValueError("Measurement value must be provided and cannot be empty.")
        if not unit:
            raise ValueError("Measurement unit must be provided and cannot be empty.")
        if not valid_start_time:
            raise ValueError("Measurement valid start time must be provided and cannot be empty.")
        if not component and not loinc_num:
            raise ValueError("You must provide at least a LOINC code or a component name in order to update a measurement.")
        
        # Input cleanup
        patient_id = str(patient_id).strip()
        loinc_num = str(loinc_num).strip() if loinc_num else None
        component = str(component).strip() if component else None
        value = str(value).strip()
        unit = str(unit).strip()
        valid_start_time = str(valid_start_time).strip()
        transaction_time = str(transaction_time).strip() if transaction_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Validate dates
        valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        transaction_time = validate_datetime(transaction_time).strftime('%Y-%m-%d %H:%M:%S')
        validate_dates_relation(valid_start_time, transaction_time, 'Valid Start Date', 'Transaction Insertion Time')

        # Verify input
        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")
        
        # CASE 1: Both LOINC and Component provided → check match
        if loinc_num and component:
            loinc_num_1 = loinc_num
            matching_loinc_codes = data.fetch_records(GET_LOINC_BY_COMPONENT_FL_QUERY, (component,))
            if not matching_loinc_codes:
                raise ValueError(f"No LOINC code found for component '{component}' in LOINC table. Check the LOINC repository to fetch the correct code / name of the intended concept.")                 
            matching_loinc_codes = [code[0] for code in matching_loinc_codes] # Extract from tuples
            if not loinc_num_1 in matching_loinc_codes:
                raise ValueError(f"LOINC code '{loinc_num_1}' and component '{component}' do not match. The input component returned Loinc-Codes={matching_loinc_codes}. Check the LOINC repository to fetch the correct code / name of the intended concept.")
        
        # CASE 2: Only Component provided → look up LOINC code from the full LOINC table
        elif component and not loinc_num:
            matching_loinc_codes = data.fetch_records(GET_LOINC_BY_COMPONENT_FL_QUERY, (component,))
            if not matching_loinc_codes:
                raise ValueError(f"No LOINC code found for component '{component}' in LOINC table. Check the LOINC repository to fetch the correct code / name of the intended concept.")  
            matching_loinc_codes = [code[0] for code in matching_loinc_codes] # Extract from tuples
            if len(matching_loinc_codes)> 1:
                raise ValueError(f"The component name you inserted returned more than 1 code, so the system does not know which code to use. Please insert the exact code you want to use.")
            loinc_num = str(matching_loinc_codes[0]).strip()
        
        # CASE 3: Only LOINC-Code provided → continue as usual
        elif loinc_num:
            if not data.check_record(CHECK_LOINC_QUERY, (loinc_num,)):
                raise LoincCodeNotFound("LOINC code not found in LOINC table.")

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
        # Verify input
        if not patient_id:
            raise ValueError("Patient ID must be provided and cannot be empty.")
        if not new_value:
            raise ValueError("Measurement new value must be provided and cannot be empty.")
        if not valid_start_time:
            raise ValueError("Measurement valid start time must be provided and cannot be empty.")
        if not component and not loinc_num:
            raise ValueError("You must provide at least a LOINC code or a component name in order to update a measurement.")
        
        # Input cleanup
        patient_id = str(patient_id).strip()
        loinc_num = str(loinc_num).strip() if loinc_num else None
        component = str(component).strip() if component else None
        valid_start_time = str(valid_start_time).strip()
        new_value = str(new_value).strip()
        valid_start_time = str(valid_start_time).strip()
        transaction_time = str(transaction_time).strip() if transaction_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Validate dates
        valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        transaction_time = validate_datetime(transaction_time).strftime('%Y-%m-%d %H:%M:%S')
        validate_dates_relation(valid_start_time, transaction_time, 'Valid Start Date', 'Transaction Insertion Time')
        

        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")

        # CASE 1: Both LOINC and Component provided → check match
        if loinc_num and component:
            loinc_num_1 = loinc_num
            matching_loinc_codes = data.fetch_records(GET_LOINC_BY_COMPONENT_FM_QUERY, (component, patient_id, valid_start_time, transaction_time))
            if not matching_loinc_codes:
                raise ValueError(f"No LOINC code found for component '{component}' in the patient's data at the provided date. Check the Show History screen to fetch the correct code / name of the intended concept.") 
            matching_loinc_codes = [code[0] for code in matching_loinc_codes] # Extract from tuples
            if not loinc_num_1 in matching_loinc_codes:
                raise ValueError(f"LOINC code '{loinc_num_1}' and component '{component}' do not match. The input component returned Loinc-Codes={matching_loinc_codes}. Check the LOINC repository to fetch the correct code / name of the intended concept.")
        
        # CASE 2: Only Component provided → look up LOINC code from the the patient's measurements table (you can only change an existing code)
        elif component and not loinc_num:
            matching_loinc_codes = data.fetch_records(GET_LOINC_BY_COMPONENT_FM_QUERY, (component, patient_id, valid_start_time, transaction_time))
            if not matching_loinc_codes:
                raise ValueError(f"No LOINC code found for component '{component}' in the patient's data at the provided date. Check the Show History screen to fetch the correct code / name of the intended concept.")   
            matching_loinc_codes = [code[0] for code in matching_loinc_codes] # Extract from tuples
            if len(matching_loinc_codes)> 1:
                raise ValueError(f"The component name you inserted returned more than 1 code, so the system does not know which code to use. Please insert the exact code you want to use.")
            loinc_num = str(matching_loinc_codes[0]).strip()

        # CASE 3: Only LOINC-Code provided → continue as usual
        elif loinc_num:
            if not data.check_record(CHECK_LOINC_QUERY, (loinc_num,)):
                raise LoincCodeNotFound("LOINC code not found in LOINC table.")
        
        # Check if this record doesn't exists (and needs to be handled with insert, not update)
        if not data.check_record(CHECK_RECORD_QUERY, (patient_id, loinc_num, valid_start_time, transaction_time)):
            raise RecordNotFound("This record was not found in the DB. If this record should exist - maybe you used an irrelevant DB snapshot? (with Transaction time), else - please use the Insert Measurement tab")

        # In case transaction_time is not the most updated TransactionInsertionTime for this record, get the TransactionDeletionDate for it
        # deletion_date can be None
        future_record_date = data.get_attr(CHECK_FUTURE_RECORD_QUERY, (patient_id, loinc_num, valid_start_time, transaction_time))
        future_record_date = str(future_record_date).strip() if future_record_date else future_record_date
        if future_record_date:
            raise ValueError(f"This record has a newer update from {future_record_date} and cannot be updated to an unupdated version (date): {transaction_time}.")
        
        # Fetch the unit from existing records, to save input from the client.
        unit = str(data.get_attr(GET_EXISTING_UNIT_QUERY, (patient_id, loinc_num, valid_start_time))).strip()
        # No exception in case non found, as that's the reflection of this concept in the DB.

        # Update end time on older records
        data.execute_query(
            UPDATE_DELETION_TIME_QUERY,
            (patient_id, loinc_num, valid_start_time, transaction_time, transaction_time, transaction_time)
        )
        
        # Insert the new measurement row
        data.execute_query(
            INSERT_MEASUREMENT_QUERY,
            (patient_id, loinc_num, new_value, unit, valid_start_time, transaction_time)
        )

    @staticmethod
    def delete_measurement(patient_id, valid_start_time, loinc_num=None, component=None, deletion_time=None):
        """
        Logically deletes a measurement (sets TransactionDeletionTime).

        - Uses LOINC code or component name to identify the measurement.
        - Verifies that the record isn't already deleted.
        - Returns the record before deletion for confirmation.
        """
        # Verify input
        if not patient_id:
            raise ValueError("Patient ID must be provided and cannot be empty.")
        if not valid_start_time:
            raise ValueError("Measurement valid start time must be provided and cannot be empty.")
        if not component and not loinc_num:
            raise ValueError("You must provide at least a LOINC code or a component name in order to update a measurement.")
        
        # Input cleanup
        patient_id = str(patient_id).strip()
        loinc_num = str(loinc_num).strip()
        component = str(component).strip()
        valid_start_time = str(valid_start_time).strip()
        deletion_time = str(validate_datetime(deletion_time).strftime('%Y-%m-%d %H:%M:%S')).strip() if deletion_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Validate and process dates
        # If only a date was given, get the latest ValidStartTime on that date
        if len(valid_start_time) <= 10:
            input_date = validate_datetime(valid_start_time).strftime('%Y-%m-%d') # Allow date to be date only, not ISO, as requested.
            result = data.get_attr(GET_LATEST_VALIDTIME_FOR_DAY_QUERY, (patient_id, loinc_num, input_date, deletion_time))
            if not result:
                raise RecordNotFound(f"No measurement found for patient {patient_id} on {input_date} for LOINC-Code {loinc_num}. Be sure that the record was not deleted in TransactionDeletionTime.")
            valid_start_time = str(validate_datetime(result).strftime('%Y-%m-%d %H:%M:%S')).strip()
        else:
            # Input was a date-time and will be treated as such
            validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        
        validate_dates_relation(valid_start_time, deletion_time, 'Valid Start Date', 'Transaction Deletion Time')

        # Validate patient
        if not data.check_record(CHECK_PATIENT_BY_ID_QUERY, (patient_id,)):
            raise PatientNotFound("Patient not found")

        # CASE 1: Both LOINC and Component provided → check match
        if loinc_num and component:
            loinc_num_1 = loinc_num
            matching_loinc_codes = data.fetch_records(GET_LOINC_BY_COMPONENT_FM_QUERY, (component, patient_id, valid_start_time, deletion_time))
            if not matching_loinc_codes:
                raise ValueError(f"No LOINC code found for component '{component}' in the patient's data at the provided date. Check the Show History screen to fetch the correct code / name of the intended concept.")  
            matching_loinc_codes = [code[0] for code in matching_loinc_codes] # Extract from tuples
            if not loinc_num_1 in matching_loinc_codes:
                raise ValueError(f"LOINC code '{loinc_num_1}' and component '{component}' do not match. The input component returned Loinc-Codes={matching_loinc_codes}. Check the LOINC repository to fetch the correct code / name of the intended concept.")
        
        # CASE 2: Only Component provided → look up LOINC code from the the patient's measurements table (you can only change an existing code)
        elif component and not loinc_num:
            matching_loinc_codes = data.fetch_records(GET_LOINC_BY_COMPONENT_FM_QUERY, (component, patient_id, valid_start_time, deletion_time))
            if not matching_loinc_codes:
                raise ValueError(f"No LOINC code found for component '{component}' in the patient's data at the provided date. Check the Show History screen to fetch the correct code / name of the intended concept.") 
            matching_loinc_codes = [code[0] for code in matching_loinc_codes] # Extract from tuples
            if len(matching_loinc_codes)> 1:
                raise ValueError(f"The component name you inserted returned more than 1 code, so the system does not know which code to use. Please insert the exact code you want to use.")
            loinc_num = str(matching_loinc_codes[0]).strip()
        
        # CASE 3: Only LOINC-Code provided → continue as usual
        elif loinc_num:
            loinc_num = str(loinc_num).strip()
            if not data.check_record(CHECK_LOINC_QUERY, (loinc_num,)):
                raise LoincCodeNotFound("Loinc code not found")
        
        else:
            raise ValueError("You must provide at least a LOINC code or a component name in order to update a measurement.")

        # Check if record exists in the desired snapshot. One cannot delete an already deleted record at past time.
        if not data.check_record(CHECK_RECORD_QUERY, (patient_id, loinc_num, valid_start_time, deletion_time)):
            print('Error deleting: ', (patient_id, loinc_num, valid_start_time, deletion_time))
            raise RecordNotFound("This record could not be found in the DB, at the date you wish to delete it.")
        
                # In case transaction_time is not the most updated TransactionInsertionTime for this record, get the TransactionDeletionDate for it
        # deletion_date can be None
        future_record_date = data.get_attr(CHECK_FUTURE_RECORD_QUERY, (patient_id, loinc_num, valid_start_time, deletion_time))
        future_record_date = str(future_record_date).strip() if future_record_date else future_record_date
        if future_record_date:
            raise ValueError(f"This record has a newer update from {future_record_date} meaning you cannot delete an unupdated version at: {deletion_time}. \nPlease contact your system admin if you need to remove this record from all DB history snapshots.")

        # Update end time on older records
        data.execute_query(
            UPDATE_DELETION_TIME_QUERY,
            (patient_id, loinc_num, valid_start_time, deletion_time, deletion_time, deletion_time)
        )
    

if __name__ == "__main__":
    import sys

    print("🔍 Running business logic tests...")

    record = PatientRecord()

    # try:
    #     first_name, last_name = "Eyal", "Rothman"
    #     print("\n🧪 Test 1: Get patient by name (should succeed)...")
    #     result = record.get_patient_by_name(first_name, last_name)
    #     for r in result:
    #         print(f"✅ Found: ID={r[0]}, FirstName={r[1]}, LastName={r[2]}")
    # except Exception as e:
    #     print(f"❌ Test 1 failed: {e}")
    #     print("Testing raw fetch...")
    #     rows = data.fetch_records(CHECK_PATIENT_BY_NAME_QUERY, (first_name, last_name))
    #     print("Result from DB:", rows)
    #     if not rows:
    #         rows = data.fetch_records('SELECT * FROM Patients', ())
    #         print("All patients from DB:", rows)
    #     sys.exit(1)

    # try:
    #     print("\n🧪 Test 2: Search history with snapshot and range...")
    #     history = record.search_history(
    #         patient_id="345678904",
    #         snapshot_date="01/01/2024 12:00",
    #         start="01/01/2000",
    #         end="02/01/2023"
    #     )
    #     print(f"✅ Found {len(history)} records")
    #     for row in history:
    #         print("   ", row)
    # except Exception as e:
    #     print(f"❌ Test 2 failed: {e}")
    #     sys.exit(1)

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

    # print("\n✅ All tests completed successfully!")

    try:
        print("\n🧪 Test 5: update measurement...")
        # query = """
        #         DELETE FROM Measurements WHERE PatientId=208388918 AND ValidStartTime='2025-05-01 12:00:00'
        #         """
        # res = data.execute_query(query, ())
        query = """
                SELECT * FROM Measurements WHERE PatientId=208388918
                """
        res = data.fetch_records(query, ())
        for rec in res:
            print(rec)

    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        sys.exit(1)

    print("\n✅ All tests completed successfully!")

