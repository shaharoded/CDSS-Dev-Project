SELECT
    m.LoincNum,
    l.Component,
    m.Value,
    m.Unit,
    m.ValidStartTime,
    m.TransactionTime
FROM Measurements m
JOIN Loinc l ON m.LoincNum = l.LoincNum
WHERE m.PatientID = ? AND m.LoincNum = ? AND m.ValidStartTime = ?;