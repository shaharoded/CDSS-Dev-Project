"""
Business Logic Layer for CDSS Project.

Handles all patient-related operations by combining
SQL queries and data access functions.

All SQL queries are saved separately under /queries/
"""

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

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def insert_measurement(self, loinc_num, value, unit, valid_start_time, transaction_time):
        """
        Insert a new measurement for a patient.

        - Use CHECK_PATIENT_QUERY to get patient_id.
        - Insert measurement using INSERT_MEASUREMENT_QUERY.
        - Raise PatientNotFound if not exists.
        """
        pass

    @staticmethod
    def search_history(first_name, last_name, loinc_num=None, date_range=None, time_range=None):
        """
        Search patient measurement history.

        - Use CHECK_PATIENT_QUERY to fetch patient_id.
        - Dynamically build WHERE clause based on filters.
        - Execute SEARCH_HISTORY_QUERY.
        - Return the results.

        NOTE: Query file is preforming a Join operation to fetch the LOINC concept name from LOINC table.
        """

        # Fetch patient_id
        patient = data._fetch_records(CHECK_PATIENT_QUERY, (first_name, last_name))
        if not patient:
            raise PatientNotFound("Patient not found")
        patient_id = patient[0][0]

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
    def update_measurement(first_name, last_name, loinc_num, valid_start_time, new_value):
        """
        Update an existing measurement value.

        - Use CHECK_PATIENT_QUERY to verify existence.
        - Update value using UPDATE_MEASUREMENT_QUERY.
        - Handle edge cases: no matching record.
        """
        pass

    @staticmethod
    def delete_measurement(first_name, last_name, loinc_num, valid_start_time):
        """
        Delete a specific measurement.

        - Use CHECK_PATIENT_QUERY to verify existence.
        - Delete using DELETE_MEASUREMENT_QUERY.
        - Handle edge cases: no matching record.
        """
        pass

# Local Tests
if __name__ == '__main__':
    print("Running local tests...")

    # Try fetching history for an existing patient
    result = PatientRecord.search_history("Eyal", "Rothman")
    print("History for Eyal Rothman:")
    for row in result:
        print(row)