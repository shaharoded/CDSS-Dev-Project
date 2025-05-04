DELETE FROM Measurements
WHERE PatientID = ?
  AND LoincNum = ?
  AND ValidStartTime = ?;