
import sqlite3
import os
import pandas as pd
import zipfile
import shutil

# Local Code
from backend.backend_config import *


class DataAccess:
    def __init__(self, db_path='cdss.db'):
        '''
        Initialize the DataAccess class, connecting to the SQLite database and creating tables if they don't exist.
        :param db_path: The path to the SQLite database file.
        '''
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()

        if not self._check_tables_exist():
            self._execute_script(INITIATE_PATIENTS_TABLE_DDL)
            self._execute_script(INITIATE_LOINC_TABLE_DDL)
            self._load_patients_from_excel()
            self._load_loinc_from_zip()
            self._print_db_info()

    def _execute_script(self, script_path):
        """
        Execute a DDL script from a file.
        Used to initialize tables in the DB.
        """
        with open(script_path, 'r') as file:
            script = file.read()
        self.cur.executescript(script)
        self.conn.commit()

    def _execute_query(self, query_path, params):
        """
        Execute a query with parameters from a file.
        Query execution -> INSERT, UPDATE, DELETE queries.
        Used to load data to initialized tables in the DB.
        """
        with open(query_path, 'r') as file:
            query = file.read()
        self.cur.execute(query, params)
        self.conn.commit()
    
    def _fetch_records(self, query_path, params):
        """
        Returning records from a query with parameters from a file.
        Query fetched -> SELECT queries.
        Used to return data from filled tables in the DB.
        """
        with open(query_path, 'r') as file:
            query = file.read()
        return self.cur.execute(query, params).fetchall()

    def _check_tables_exist(self):
        """
        Ensuring DB was initialized
        """
        result = self._fetch_records(CHECK_TABLE_EXISTS_QUERY, ())
        return bool(result)

    def _load_patients_from_excel(self):
        """
        Load patients from an Excel file and insert them into the Patients table.
        """
        df = pd.read_excel(PATIENTS_FILE)

        if df.empty:
            print('[Info]: No patients data found to load.')
            return

        for _, row in df.iterrows():
            self._execute_query(INSERT_PARIENT_QUERY, (row['First name'], row['Last name']))
            patient_id = self._fetch_records(CHECK_PATIENT_QUERY, (row['First name'], row['Last name']))[0][0]
            self._execute_query(
                INSERT_MEASUREMENT_QUERY,
                (
                    patient_id,
                    row['LOINC-NUM'],
                    row['Value'],
                    row['Unit'],
                    str(row['Valid start time']),
                    str(row['Transaction time'])
                )
            )

        print(f'[Info]: Loaded {len(df)} records from Excel file to DB tables.')

    def _load_loinc_from_zip(self):
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
                self._execute_query(
                    INSET_LOINC_CODE_QUERY,
                    (row['LOINC_NUM'], row['COMPONENT'], row['PROPERTY'], row['TIME_ASPCT'],
                    row['SYSTEM'], row['SCALE_TYP'], row['METHOD_TYP'])
                )
            print(f'[Info]: Loaded {len(df)} LOINC codes from ZIP.')

        shutil.rmtree(extract_path)
        
    def _print_db_info(self):
        """
        Printing DB information, including the total number of tables created and the number of rows in each table.
        """
        print("[Info]: DB initiated successfully!")
        
        tables = self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()

        print(f"[Info]: Total tables created: {len(tables)}")

        for (table_name,) in tables:
            count = self.cur.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]
            print(f"[Info]: Table '{table_name}' - Rows: {count}")

if __name__ == '__main__':
    da = DataAccess()

