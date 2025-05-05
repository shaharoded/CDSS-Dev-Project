UPDATE Measurements
SET TransactionDeletionTime = ?
WHERE PatientId = ?
  AND LoincNum = ?
  AND ValidStartTime = ?
  AND TransactionInsertionTime < ?
  AND (TransactionDeletionTime IS NULL OR TransactionDeletionTime > ?);
