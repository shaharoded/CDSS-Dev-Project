-- Purpose: Find the current record and set it's TransactionDeletionTime to the TransactionInsertionTime of the new record 
-- Uses a sub-query to utilize ORDER BY and LIMIT in order to find the most current version of the record.

UPDATE Measurements
SET TransactionDeletionTime = ?
WHERE rowid = (
    SELECT rowid FROM Measurements
    WHERE PatientId = ?
      AND LoincNum = ?
      AND DATE(ValidStartTime) = ?
      AND TransactionInsertionTime < ?
      AND (TransactionDeletionTime IS NULL OR DATE(TransactionDeletionTime) > ?)
    ORDER BY DATE(TransactionInsertionTime) DESC
    LIMIT 1
);