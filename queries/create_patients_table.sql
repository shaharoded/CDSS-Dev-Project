-- Purpose: Creates 2 tables to manage the patients in the file

CREATE TABLE IF NOT EXISTS Patients (
    PatientId INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT,
    LastName TEXT
);

CREATE TABLE IF NOT EXISTS Measurements (
    MeasurementId INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientId INTEGER,
    LoincNum TEXT,
    Value TEXT,
    Unit TEXT,
    ValidStartTime TEXT,
    TransactionTime TEXT,
    FOREIGN KEY (PatientId) REFERENCES Patients(PatientId)
);
