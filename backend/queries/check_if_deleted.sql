SELECT TransactionDeletionTime
FROM Measurements
WHERE PatientId = ? AND LoincNum = ? AND ValidStartTime = ?;