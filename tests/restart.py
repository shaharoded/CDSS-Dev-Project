from backend.dataaccess import DataAccess

data = DataAccess()
data.cur.execute("DROP TABLE IF EXISTS Measurements;")
data.cur.execute("DROP TABLE IF EXISTS Patients;")
data.conn.commit()
print("[INFO] Dropped Patients and Measurements tables.")


# Create Patients table
data.cur.execute("""
CREATE TABLE IF NOT EXISTS Patients (
    PatientId TEXT PRIMARY KEY,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL
);
""")
print("[INFO] Created Patients table.")

# Create Measurements table
data.cur.execute("""

CREATE TABLE IF NOT EXISTS Measurements (
    MeasurementId INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientId TEXT,
    LoincNum TEXT,
    Value TEXT NOT NULL,
    Unit TEXT,
    ValidStartTime TEXT NOT NULL,
    TransactionInsertionTime TEXT NOT NULL, -- The time a record was inserted to the DB
    TransactionDeletionTime TEXT, -- The time a record was deleted from the DB
    FOREIGN KEY (PatientId) REFERENCES Patients(PatientId),
    FOREIGN KEY (LoincNum) REFERENCES Loinc(LoincNum)
);
""")
print("[INFO] Created Measurements table.")

# Commit changes
data.conn.commit()
print("[INFO] Database schema creation complete.")

# Load SQL from file
from backend.dataaccess import DataAccess
data = DataAccess()
data._DataAccess__load_patients_from_excel()
data._DataAccess__load_loinc_from_zip()