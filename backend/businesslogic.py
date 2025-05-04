"""
Business Logic Layer for CDSS Project.

Handles all patient-related operations by combining
SQL queries and data access functions.

All SQL queries are saved separately under /queries/
"""

# Local Code
from backend.dataaccess import DataAccess
from backend.backend_config import *  # all query paths

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

    def check_patient(self):
        # Check if PatientId exists (without name check)
        patient_by_id = data._fetch_records(CHECK_PATIENT_BY_ID_QUERY, (self.patient_id,))
        if patient_by_id:
            db_first, db_last = patient_by_id[0]
            return db_first, db_last  # Return name from DB
        return None

    def register_patient(self):
        # Insert new patient
        data._execute_query(INSERT_PATIENT_QUERY, (self.first_name, self.last_name, self.patient_id))
        # DEBUG: Check if patient was inserted
        print("DEBUG: Patients in DB:", data.cur.execute("SELECT * FROM Patients").fetchall())

    def insert_measurement(self, loinc_num, value, unit, valid_start_time, transaction_time):
        """
        Insert a new measurement for a patient.

        - Use CHECK_PATIENT_QUERY to get patient_id.
        - Insert measurement using INSERT_MEASUREMENT_QUERY.
        - Raise PatientNotFound if not exists.
        """
        patient = data._fetch_records(CHECK_PATIENT_QUERY, (self.patient_id, self.first_name, self.last_name))
        if not patient:
            raise PatientNotFound("Patient not found")

            # Insert measurement
        data._execute_query(
            INSERT_MEASUREMENT_QUERY,
            (self.patient_id, loinc_num, value, unit, valid_start_time, transaction_time)
        )

    @staticmethod
    def search_history(patient_id, first_name, last_name, loinc_num=None, date_range=None, time_range=None):
        """
        Search patient measurement history.

        - Use CHECK_PATIENT_QUERY to fetch patient_id.
        - Dynamically build WHERE clause based on filters.
        - Execute SEARCH_HISTORY_QUERY.
        - Return the results.

        NOTE: Query file is preforming a Join operation to fetch the LOINC concept name from LOINC table.

        NOTE: Index is not an id
        """

        # Fetch patient_id
        patient = data._fetch_records(CHECK_PATIENT_BY_ID_QUERY, (patient_id,))
        if not patient:
            raise PatientNotFound("Patient not found")
        #patient_id = patient[0][0] #just the index of the patient in the array, not a unique id for the patient
        patient_id = patient_id
        print(f"this is the id {patient_id}")

        # Build dynamic filters
        filters = []
        params = [patient_id]

        if loinc_num:
            filters.append("LoincNum = ?")
            params.append(loinc_num)

        if date_range:
            filters.append("DATE(ValidStartTime) BETWEEN ? AND ?")
            params.extend(date_range)

        if time_range:
            filters.append("TIME(ValidStartTime) BETWEEN ? AND ?")
            params.extend(time_range)

        where_clause = " AND ".join(filters) if filters else "1=1"

        # Read base query
        with open(SEARCH_HISTORY_QUERY, 'r') as f:
            base_query = f.read()

        final_query = base_query.replace("{where_clause}", where_clause)

        result = data.cur.execute(final_query, params).fetchall()
        return result

    @staticmethod
    def update_measurement(patient_id, first_name, last_name, loinc_num, valid_start_time, new_value):
        """
        Update an existing measurement value.

        - Use CHECK_PATIENT_QUERY to verify existence.
        - Update value using UPDATE_MEASUREMENT_QUERY.
        - Handle edge cases: no matching record.
        """
        # Verify patient exists
        patient = data._fetch_records(CHECK_PATIENT_QUERY, (patient_id, first_name, last_name))
        if not patient:
            raise PatientNotFound("Patient not found")

        print(f"this is the id {patient_id}")

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

        # Update the measurement value using _execute_query
        data._execute_query(
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

