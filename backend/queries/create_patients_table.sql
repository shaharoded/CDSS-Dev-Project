-- Purpose: Creates 2 tables to manage the patients in the file

CREATE TABLE IF NOT EXISTS Patients (
    FirstName TEXT,
    LastName TEXT,
    PatientId TEXT PRIMARY KEY
);


CREATE TABLE IF NOT EXISTS Measurements (
    MeasurementId INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientId TEXT,
    LoincNum TEXT,
    Value TEXT,
    Unit TEXT,
    ValidStartTime TEXT,
    TransactionTime TEXT,
    FOREIGN KEY (PatientId) REFERENCES Patients(PatientId),
    FOREIGN KEY (LoincNum) REFERENCES Loinc(LoincNum)
);
