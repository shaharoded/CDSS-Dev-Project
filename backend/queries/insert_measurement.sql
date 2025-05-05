INSERT INTO Measurements (
    PatientId,
    LoincNum,
    Value,
    Unit,
    ValidStartTime,
    TransactionInsertionTime,
    TransactionDeletionTime #added
)
VALUES (?, ?, ?, ?, ?, ?, NULL);
