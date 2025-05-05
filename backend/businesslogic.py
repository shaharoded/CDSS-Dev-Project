"""
Business Logic Layer for CDSS Project.

Handles all patient-related operations by combining
SQL queries and data access functions.

All SQL queries are saved separately under /queries/
"""
import pandas as pd

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
    if not name.isalpha():
        raise ValueError(f"{field_name} must contain alphabetic characters only.")

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
        if not data.check_patient(patient_id):
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
            start_dt = validate_datetime(start)
            if start_dt.time() == pd.Timestamp.min.time():  # no time provided
                start_iso = start_dt.replace(hour=0, minute=0, second=0)
            else:
                start_iso = start_dt
            filters.append("m.ValidStartTime >= ?")
            params.append(start_iso.strftime('%Y-%m-%d %H:%M:%S'))

        if end:
            end_dt = validate_datetime(end)
            if end_dt.time() == pd.Timestamp.min.time():  # no time provided
                end_iso = end_dt.replace(hour=23, minute=59, second=59)
            else:
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
        if data.check_patient(patient_id):
            raise ValueError("You tried to input an existing patient into the system.\nUse the search tab to verify your input.")
        validate_patient_id(patient_id)
        validate_name(first_name, 'First Name')
        validate_name(last_name, 'Last Name')
        
        # Insert new patient
        data.execute_query(INSERT_PATIENT_QUERY, (patient_id, first_name, last_name))
    
    @staticmethod
    def insert_measurement(patient_id, loinc_num, value, unit, valid_start_time, transaction_time=None):
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

        # Validations
        if not data.check_patient(patient_id):
            raise PatientNotFound("Patient not found")
        if not data.check_loinc(loinc_num):
            raise LoincCodeNotFound("Loinc code not found")
        valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        transaction_time = validate_datetime(transaction_time).strftime('%Y-%m-%d %H:%M:%S')
        validate_dates_relation(valid_start_time, transaction_time, 'Valid Start Date', 'Transaction Insertion Time')

        # In case transaction_time is not the most updated TransactionInsertionTime for this record, get the TransactionDeletionDate for it
        # deletion_date can be None
        future_record_date = data.get_future_record_time(patient_id, loinc_num, valid_start_time, transaction_time)
        if future_record_date:
            raise ValueError(f"This record has a newer update from {future_record_date} and cannot be updated to an unupdated version.")

        # Insert measurement
        data.execute_query(
            INSERT_MEASUREMENT_QUERY,
            (patient_id, loinc_num, value, unit, valid_start_time, transaction_time)
        )

    @staticmethod
    def update_measurement(patient_id, loinc_num, valid_start_time, new_value, transaction_time=None):
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
        if not data.check_patient(patient_id):
            raise PatientNotFound("Patient not found")
        if not data.check_loinc(loinc_num):
            raise LoincCodeNotFound("Loinc code not found")
        valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        transaction_time = validate_datetime(transaction_time).strftime('%Y-%m-%d %H:%M:%S')
        validate_dates_relation(valid_start_time, transaction_time, 'Valid Start Date', 'Transaction Insertion Time')
        if not data.check_record(patient_id, loinc_num, valid_start_time):
            raise RecordNotFound("This record was not found in the DB")

        # Update the measurement value using execute_query
        data.execute_query(
            UPDATE_MEASUREMENT_QUERY,
            (new_value, patient_id, loinc_num, valid_start_time)
        )

    @staticmethod
    def delete_measurement(patient_id, loinc_num, valid_start_time):
        """
        Delete a specific measurement.

        - Use CHECK_PATIENT_QUERY to verify existence.
        - Delete using DELETE_MEASUREMENT_QUERY.
        - Handle edge cases: no matching record.
        """
        # Input cleanup
        patient_id = str(patient_id).strip()
        loinc_num = str(loinc_num).strip()
        valid_start_time = str(valid_start_time).strip()
        
        # Verify input
        if not data.check_patient(patient_id):
            raise PatientNotFound("Patient not found")
        if not data.check_loinc(loinc_num):
            raise LoincCodeNotFound("Loinc code not found")
        valid_start_time = validate_datetime(valid_start_time).strftime('%Y-%m-%d %H:%M:%S')
        if not data.check_record(patient_id, loinc_num, valid_start_time):
            raise RecordNotFound("This record was not found in the DB")
        
        # Continue from here
        raise NotImplementedError("Update measurement not implemented yet")
    

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

    try:
        print("\n🧪 Test 3: Register a new patient (should succeed or fail if already exists)...")
        record.register_patient("123456789", "Alice", "Smith")
        print("✅ Registered patient successfully")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        sys.exit(1)

    try:
        print("\n🧪 Test 4: Insert measurement (should validate and insert)...")
        record.insert_measurement(
            patient_id="123456789",
            loinc_num="718-7",
            value="14.2",
            unit="mmol/L",
            valid_start_time="01/04/2024 08:00",
            transaction_time="01/04/2024 08:01"
        )
        print("✅ Inserted measurement")
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        sys.exit(1)

    print("\n✅ All tests completed successfully!")

