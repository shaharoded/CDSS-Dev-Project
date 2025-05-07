SELECT ValidStartTime
FROM Measurements
WHERE PatientId = ? AND LoincNum = ? AND DATE(ValidStartTime) = ?
ORDER BY ValidStartTime DESC
LIMIT 1;