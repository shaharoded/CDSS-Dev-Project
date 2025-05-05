-- Purpose: Creates 2 tables to manage the patients in the file

CREATE TABLE IF NOT EXISTS Patients (
    PatientId TEXT PRIMARY KEY
    FirstName TEXT,
    LastName TEXT
);


CREATE TABLE IF NOT EXISTS Measurements (
    MeasurementId TEXT PRIMARY KEY AUTOINCREMENT,
    PatientId TEXT,
    LoincNum TEXT,
    Value TEXT NOT NULL,
    Unit TEXT,
    ValidStartTime TEXT NOT NULL,
    TransactionStartTime TEXT NOT NULL,
    TransactionEndTime TEXT,
    FOREIGN KEY (PatientId) REFERENCES Patients(PatientId),
    FOREIGN KEY (LoincNum) REFERENCES Loinc(LoincNum)
);
