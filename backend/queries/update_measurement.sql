-- Purpose: To update a measurement based on it's PatientId, LoincNum and ValidStartTime
-- If more than 1 record fits this condition, we'll update the one last inputed into the DB (based on TransactionTime)

UPDATE Measurements
SET Value = ?
WHERE PatientId = ?
  AND LoincNum = ?
  AND ValidStartTime = ?;
