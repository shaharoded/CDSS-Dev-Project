INSERT INTO Measurements (
    PatientId,
    LoincNum,
    Value,
    Unit,
    ValidStartTime,
    TransactionInsertionTime,
    TransactionDeletionTime
)
VALUES (?, ?, ?, ?, ?, ?, NULL);
