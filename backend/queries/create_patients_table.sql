-- Purpose: Creates 2 tables to manage the patients in the file

CREATE TABLE IF NOT EXISTS Patients (
    PatientId TEXT PRIMARY KEY,
    FirstName TEXT,
    LastName TEXT,
    Sex TEXT
);


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
