SELECT PatientId, LoincNum, ValidStartTime, TransactionDeletionTime
FROM Measurements
WHERE PatientId = ? AND LoincNum = ? AND ValidStartTime = ?