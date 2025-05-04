import os

# Get project root (one level up from backend/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

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
CHECK_PATIENT_BY_ID_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_patient_by_id.sql')


# SQL Queries
CHECK_PATIENT_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_patient.sql')
CHECK_TABLE_EXISTS_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'check_table_exists.sql')
SEARCH_HISTORY_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'get_history.sql')
UPDATE_MEASUREMENT_QUERY = os.path.join(PROJECT_ROOT, 'backend', 'queries', 'update_measurement.sql')
