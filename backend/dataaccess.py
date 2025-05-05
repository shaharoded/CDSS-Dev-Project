
import sqlite3
import os
import pandas as pd
import zipfile
import shutil

# Local Code
from backend.backend_config import *


class DataAccess:
    def __init__(self, db_path=DB_PATH):
        '''
        Initialize the DataAccess class, connecting to the SQLite database and creating tables if they don't exist.
        :param db_path: The path to the SQLite database file.

        Args:
            db_path (str): The path to the SQLite database file. Configured in backend_config.py.
        '''
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()

        if not self.__check_tables_exist():
            self.__execute_script(INITIATE_PATIENTS_TABLE_DDL)
            self.__execute_script(INITIATE_LOINC_TABLE_DDL)
            self.__load_patients_from_excel()
            self.__load_loinc_from_zip()
            self.__print_db_info()

    def check_patient(self, patient_id):
        """
        Returns True if the given PatientId exists in the database.
        """
        result = self.fetch_records(CHECK_PATIENT_BY_ID_QUERY, (patient_id,))
        return bool(result)
    
    def check_loinc(self, loinc_code):
        """
        Returns True if the given Loinc-code exists in the database.
        """
        result = self.fetch_records(CHECK_LOINC_QUERY, (loinc_code,))
        return bool(result)
    
    def check_record(self, patient_id, loinc_code, valid_start_time, transaction_time):
        """
        Returns True if the given record exists in this snapshot of the database (described by transaction_time).
        """
        result = self.fetch_records(CHECK_RECORD_QUERY, (patient_id, loinc_code, valid_start_time, transaction_time))
        return bool(result)
    
    def get_future_record_time(self, patient_id, loinc_code, valid_start_time, transaction_time):
        """
        Returns the next TransactionInsertionTime after the one you're inserting,
        for the same (PatientId, LoincNum, ValidStartTime).
        Used to set the TransactionDeletionTime for the new backfilled record.
        Returns a string (ISO datetime) or None.
        """
        result = self.fetch_records(CHECK_FUTURE_RECORD_QUERY, (patient_id, loinc_code, valid_start_time, transaction_time))
        return result[0][0] if result else None
    
    def execute_query(self, query_or_path, params):
        """
        Executes an INSERT/UPDATE/DELETE query.
        Accepts either a path to a .sql file or a raw SQL string.
        """
        if os.path.isfile(query_or_path):
            with open(query_or_path, 'r') as file:
                query = file.read()
        else:
            query = query_or_path  # assume raw SQL

        self.cur.execute(query, params)
        self.conn.commit()
    
    def fetch_records(self, query_or_path, params):
        """
        Executes a SELECT query.
        Accepts either a path to a .sql file or a raw SQL string.
        Returns all rows.
        """
        if os.path.isfile(query_or_path):
            with open(query_or_path, 'r') as file:
                query = file.read()
        else:
            query = query_or_path  # assume raw SQL

        return self.cur.execute(query, params).fetchall()
    
    def __execute_script(self, script_path):
        """
        Execute a DDL script from a file.
        Used to initialize tables in the DB.
        """
        with open(script_path, 'r') as file:
            script = file.read()
        self.cur.executescript(script)
        self.conn.commit()

    def __check_tables_exist(self):
        """
        Ensuring DB was initialized
        """
        result = self.fetch_records(CHECK_TABLE_EXISTS_QUERY, ())
        return bool(result)

    def __load_patients_from_excel(self):
        df = pd.read_excel(PATIENTS_FILE)

        if df.empty:
            print('[Info]: No patients data found to load.')
            return
        
        # Convert datetime columns to ISO 8601 format: 'YYYY-MM-DD HH:MM:SS'
        # Drop rows where datetime conversion failed
        for col in ['Valid start time', 'Transaction time']:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True).dt.strftime('%Y-%m-%d %H:%M:%S')
        df.dropna(subset=['Valid start time', 'Transaction time'], inplace=True)

        # Deduplicate patients
        unique_patients = df[['PatientId', 'First name', 'Last name']].drop_duplicates()

        # Insert unique patients
        for _, row in unique_patients.iterrows():
            self.execute_query(
                INSERT_PATIENT_QUERY,
                (
                    str(row['PatientId']).strip(), 
                    str(row['First name']).strip().title(), 
                    str(row['Last name']).strip().title()
                )
            )

        # Insert measurements
        for _, row in df.iterrows():
            self.execute_query(
                INSERT_MEASUREMENT_QUERY,
                (
                    str(row['PatientId']).strip(),
                    str(row['LOINC-NUM']).strip(),
                    str(row['Value']).strip(),
                    str(row['Unit']).strip(),
                    str(row['Valid start time']).strip(),
                    str(row['Transaction time']).strip()
                )
            )

        print(
            f'[Info]: Loaded {len(df)} measurement records and {len(unique_patients)} unique patients from Excel file to DB tables.')

    def __load_loinc_from_zip(self):
        """
        Load LOINC codes from a ZIP file and insert them into the Loinc table in the DB for future use.
        """
        extract_path = 'data/loinc_extracted'
        with zipfile.ZipFile(LOINC_CODES_ZIP, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        loinc_file = os.path.join(extract_path, 'LoincTable', 'Loinc.csv')

        if not os.path.exists(loinc_file):
            print('[Info]: LOINC file not found in extracted ZIP.')
            return

        df = pd.read_csv(loinc_file, dtype=str)

        if df.empty:
            print('[Info]: No LOINC codes found to load.')
        else:
            for _, row in df.iterrows():
                self.execute_query(
                    INSET_LOINC_CODE_QUERY,
                    (
                        str(row['LOINC_NUM']).strip(), 
                        str(row['COMPONENT']).strip(), 
                        str(row['PROPERTY']).strip(), 
                        str(row['TIME_ASPCT']).strip(),
                        str(row['SYSTEM']).strip(), 
                        str(row['SCALE_TYP']).strip(), 
                        str(row['METHOD_TYP']).strip()
                    )
                )
            print(f'[Info]: Loaded {len(df)} LOINC codes from ZIP.')

        shutil.rmtree(extract_path)
        
    def __print_db_info(self):
        """
        Printing DB information, including the total number of tables created
        and the number of rows in each table.
        """
        print("[Info]: DB initiated successfully!")

        tables = self.fetch_records("SELECT name FROM sqlite_master WHERE type='table';", ())

        print(f"[Info]: Total tables created: {len(tables)}")

        for (table_name,) in tables:
            count = self.fetch_records(f"SELECT COUNT(*) FROM {table_name};", ())[0][0]
            print(f"[Info]: Table '{table_name}' - Rows: {count}")

if __name__ == '__main__':
    da = DataAccess()

