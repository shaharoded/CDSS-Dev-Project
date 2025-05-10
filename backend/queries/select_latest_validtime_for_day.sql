-- Purpose: Get the latest date-time of ValidStartTime, for a record at a spacific datetime.
-- Used for deletion where it's required that the user will be able to ignore time and input only date.

SELECT ValidStartTime
FROM Measurements
WHERE PatientId = ? AND LoincNum = ? AND DATE(ValidStartTime) = DATE(?)
AND (TransactionDeletionTime IS NULL OR TransactionDeletionTime > ?)
ORDER BY ValidStartTime DESC
LIMIT 1;