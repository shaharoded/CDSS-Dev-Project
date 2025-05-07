SELECT 1
FROM Measurements
WHERE PatientId = ?
  AND LoincNum = ?
  AND ValidStartTime = ?
LIMIT 1;