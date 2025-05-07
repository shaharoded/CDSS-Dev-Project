UPDATE Measurements
SET TransactionDeletionTime = ?
WHERE PatientId = ? AND LoincNum = ? AND ValidStartTime = ?;