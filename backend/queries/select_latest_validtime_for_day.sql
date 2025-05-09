SELECT ValidStartTime
FROM Measurements
WHERE PatientId = ? AND LoincNum = ? AND DATE(ValidStartTime) = ?
AND (TransactionDeletionTime IS NULL OR DATE(TransactionDeletionTime) > ?)
ORDER BY DATE(ValidStartTime) DESC
LIMIT 1;