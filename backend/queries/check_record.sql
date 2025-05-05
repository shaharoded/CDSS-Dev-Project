-- Purpose: Checks if a record exists in the DB

SELECT 1 
FROM Measurements 
WHERE PatientId = ? AND LoincNum = ? AND ValidStartTime = ?