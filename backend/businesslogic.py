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
        raise NotImplementedError("Update measurement not implemented yet")

    @staticmethod
    def delete_measurement(first_name, last_name, loinc_num=None, component_name=None, valid_start_time=None):
        """
        Delete a specific measurement for a patient.

        You may provide either `loinc_num` or `component_name`. If both are provided, `loinc_num` takes priority.

        Args:
            first_name (str): Patient's first name
            last_name (str): Patient's last name
            loinc_num (str): LOINC code (e.g., '11218-5')
            component_name (str): Component name (e.g., 'Temperature')
            valid_start_time (str): Can be full datetime or just a date (YYYY-MM-DD)

        Returns:
            list: Deleted rows (as list of tuples)
        """

        # Step 1: Check if the patient exists
        patient = data._fetch_records(CHECK_PATIENT_QUERY, (first_name, last_name))
        if not patient:
            raise PatientNotFound("Patient not found")
        patient_id = patient[0][0]

        # Step 2: Resolve LOINC number
        if not loinc_num and component_name:
            query = "SELECT LoincNum FROM Loinc WHERE Component = ? COLLATE NOCASE"
            result = data.cur.execute(query, (component_name.strip(),)).fetchone()
            if not result:
                raise ValueError(f"No LOINC code found for component '{component_name}'")
            loinc_num = result[0]

        if not loinc_num:
            raise ValueError("Must provide either LOINC code or component name.")

        # Step 3: If only a date is given, get the latest measurement on that date
        if valid_start_time and len(valid_start_time.strip()) == 10:  # YYYY-MM-DD
            date_only = valid_start_time.strip()
            with open(SELECT_LAST_MEASUREMENT_FOR_DAY_QUERY, 'r') as f:
                select_query = f.read()
            result = data.cur.execute(select_query, (patient_id, loinc_num, date_only)).fetchone()
            if not result:
                raise ValueError("No measurement found on that date.")
            valid_start_time = result[0]  # use full datetime

        # Step 4: Select row(s) to delete
        with open(SELECT_MEASUREMENT_TO_DELETE_QUERY, 'r') as f:
            preview_query = f.read()
        deleted_rows = data.cur.execute(preview_query, (patient_id, loinc_num, valid_start_time)).fetchall()
        if not deleted_rows:
            raise ValueError("No matching measurement found to delete.")

        # Step 5: Perform deletion
        with open(DELETE_MEASUREMENT_QUERY, 'r') as f:
            delete_query = f.read()
        data.cur.execute(delete_query, (patient_id, loinc_num, valid_start_time))
        data.conn.commit()

        return deleted_rows


# Local Tests
if __name__ == '__main__':
    print("Running local tests...")

    # Try fetching history for an existing patient
    result = PatientRecord.search_history("Eyal", "Rothman")
    print("History for Eyal Rothman:")
    for row in result:
        print(row)

    # result = PatientRecord.delete_measurement(
    #     first_name="Eyal",
    #     last_name="Rothman",
    #     loinc_num="76477-9",
    #     valid_start_time="2018-05-17 16:00:00"
    # )

    # for row in result:
    #     print(row)

