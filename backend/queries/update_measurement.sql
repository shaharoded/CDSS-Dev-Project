-- Purpose: Fetch PatientId by FirstName and LastName

UPDATE Measurements
SET Value = ?
WHERE PatientId = ?
  AND LoincNum = ?
  AND ValidStartTime = ?;
