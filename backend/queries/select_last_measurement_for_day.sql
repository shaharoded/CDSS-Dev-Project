SELECT ValidStartTime FROM Measurements
WHERE PatientID = ? AND LoincNum = ? AND DATE(ValidStartTime) = ?
ORDER BY ValidStartTime DESC
LIMIT 1;