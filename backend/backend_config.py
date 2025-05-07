import os

# Get project root (one level up from backend/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(PROJECT_ROOT)
# Data files
PATIENTS_FILE = os.path.join(PROJECT_ROOT, 'data', 'project_db.xlsx')
LOINC_CODES_ZIP = os.path.join(PROJECT_ROOT, 'data', 'Loinc_2.80.zip')
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'cdss.db')

# DDL Queries
INITIATE_PATIENTS_TABLE_DDL = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'create_patients_table.sql')
INITIATE_LOINC_TABLE_DDL = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'create_loinc_table.sql')

# DML Queries
INSERT_PATIENT_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'insert_patient.sql')
INSERT_MEASUREMENT_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'insert_measurement.sql')
INSET_LOINC_CODE_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'insert_loinc.sql')


# SQL Queries
CHECK_PATIENT_BY_NAME_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_patient_by_name.sql')
CHECK_PATIENT_BY_ID_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_patient_by_id.sql')
CHECK_LOINC_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_lonic.sql')
CHECK_RECORD_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_record.sql')
CHECK_FUTURE_RECORD_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_future_record.sql')
CHECK_TABLE_EXISTS_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_table_exists.sql')
SEARCH_HISTORY_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'get_history.sql')
UPDATE_MEASUREMENT_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'update_measurement.sql') # In-place value update, currently irrelevant.
UPDATE_OLD_RECORDS_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'update_old_records.sql')
GET_EXISTING_UNIT_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'get_existing_unit.sql')
GET_LOINC_BY_COMPONENT_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'get_loinc_by_component.sql')

UPDATE_RECORD_DELETION_TIME_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'update_deletion_times.sql')
CHECK_IF_DELETED_QUERY = os.path.join(PROJECT_ROOT,'backend', 'queries', "check_if_deleted.sql")
SELECT_MEASUREMENT_BEFORE_DELETE_QUERY = os.path.join(PROJECT_ROOT,'backend', 'queries', "select_measurement_before_delete.sql")
SELECT_LATEST_VALIDTIME_FOR_DAY_QUERY = os.path.join(PROJECT_ROOT,'backend', 'queries', "select_latest_validtime_for_day.sql")
CHECK_MEASUREMENT_EXISTS_QUERY = os.path.join(PROJECT_ROOT,'backend', 'queries', 'check_measurement_exists.sql')
CHECK_RECORD_FOR_DELETION = os.path.join(PROJECT_ROOT,'backend', 'queries', 'check_record_for_deletion.sql')

