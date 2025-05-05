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
import re
from datetime import datetime

data = DataAccess()


class PatientNotFound(Exception):
    """Raised when patient is not found in DB."""
    pass


class PatientRecord:
    """
    Main patient record class to handle business logic.
    """

    def __init__(self, patient_id, first_name, last_name):
        self.patient_id = patient_id
        self.first_name = first_name
        self.last_name = last_name
    
    @staticmethod
    def check_patient_by_name(first_name, last_name):
        """
        Returns the list of matching patients by their names.
        """
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

        # Fetch patient_id
        if not data.check_patient_by_id(patient_id):
            raise PatientNotFound("Patient not found")

        # Initialize dynamic filters
        filters = ["m.PatientId = ?"]
        params = [patient_id]

        if loinc_num:
            filters.append("m.LoincNum = ?")
            params.append(loinc_num)

        # Handle datetime range
        if start:
            start_dt = pd.to_datetime(start, dayfirst=True)
            if start_dt.time() == pd.Timestamp.min.time():  # no time provided
                start_iso = start_dt.replace(hour=0, minute=0, second=0)
            else:
                start_iso = start_dt
            filters.append("m.ValidStartTime >= ?")
            params.append(start_iso.strftime('%Y-%m-%d %H:%M:%S'))

        if end:
            end_dt = pd.to_datetime(end, dayfirst=True)
            if end_dt.time() == pd.Timestamp.min.time():  # no time provided
                end_iso = end_dt.replace(hour=23, minute=59, second=59)
            else:
                end_iso = end_dt
            filters.append("m.ValidStartTime <= ?")
            params.append(end_iso.strftime('%Y-%m-%d %H:%M:%S'))

        # Snapshot logic
        if snapshot_date:
            # Convert to ISO format
            snapshot_iso = pd.to_datetime(snapshot_date, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S')
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
    
    def register_patient(self):
        """
        Inserts a patient to the DB.
        """
        # Insert new patient
        data.execute_query(INSERT_PATIENT_QUERY, (self.first_name, self.last_name, self.patient_id))
        # # DEBUG: Check if patient was inserted
        # print("[DEBUG]: Patients in DB:", data.cur.execute("SELECT * FROM Patients").fetchall())

    def insert_measurement(self, loinc_num, value, unit, valid_start_time, transaction_time):
        """
        Insert a new measurement for a patient.

        - Use CHECK_PATIENT_QUERY to get patient_id.
        - Insert measurement using INSERT_MEASUREMENT_QUERY.
        - Raise PatientNotFound if not exists.
        """
        patient = data.fetch_records(CHECK_PATIENT_BY_ID_QUERY, (self.patient_id,))
        if not patient:
            raise PatientNotFound("Patient not found")

            # Insert measurement
        data.execute_query(
            INSERT_MEASUREMENT_QUERY,
            (self.patient_id, loinc_num, value, unit, valid_start_time, transaction_time)
        )

    @staticmethod
    def update_measurement(patient_id, loinc_num, valid_start_time, new_value):
        """
        Update an existing measurement value.

        - Use CHECK_PATIENT_QUERY to verify existence.
        - Update value using UPDATE_MEASUREMENT_QUERY.
        - Handle edge cases: no matching record.
        """
        # Verify patient exists
        patient = data.check_patient_by_id(patient_id)
        if not patient:
            raise PatientNotFound("Patient not found")

        # Check if measurement exists (move this SELECT query to a .sql file if you want full consistency)
        measurement_check_query = """
                SELECT 1 FROM Measurements 
                WHERE PatientId = ? AND LoincNum = ? AND ValidStartTime = ?
            """
        exists = data.cur.execute(
            measurement_check_query,
            (patient_id, loinc_num, valid_start_time)
        ).fetchall()

        if not exists:
            raise Exception("Measurement not found to update.")

        # Update the measurement value using execute_query
        data.execute_query(
            UPDATE_MEASUREMENT_QUERY,
            (new_value, patient_id, loinc_num, valid_start_time)
        )

    @staticmethod
    def delete_measurement(first_name, last_name, loinc_num, valid_start_time):
        """
        Delete a specific measurement.

        - Use CHECK_PATIENT_QUERY to verify existence.
        - Delete using DELETE_MEASUREMENT_QUERY.
        - Handle edge cases: no matching record.
        """
        raise NotImplementedError("Update measurement not implemented yet")


## ------------------ Validation Functions ------------------
def validate_patient_id(patient_id):
    if not patient_id.isdigit():
        raise ValueError("Patient ID must contain digits only.")
    if len(patient_id) != 9:
        raise ValueError("Patient ID must be exactly 9 digits long.")

def validate_name(name, field_name):
    if not name.isalpha():
        raise ValueError(f"{field_name} must contain alphabetic characters only.")

def validate_loinc(loinc_code, data_access):
    result = data.fetch_records(CHECK_LOINC_QUERY, (loinc_code,))
    if not result:
        raise ValueError(f"LOINC code '{loinc_code}' does not exist in the LOINC table.")

def validate_datetime(dt_string, field_name):
    try:
        datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"{field_name} must be in format YYYY-MM-DD HH:MM:SS.")

