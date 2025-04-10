-- Purpose: Search patient measurement history with LOINC name.
-- Params: patient_id, [loinc_num], [date_range], [time_range]

SELECT m.LoincNum,
       l.Component AS LOINCConceptName,
       m.Value,
       m.Unit,
       m.ValidStartTime,
       m.TransactionTime
FROM Measurements m
JOIN Loinc l ON m.LoincNum = l.LoincNum
WHERE m.PatientId = ?
AND {where_clause}
ORDER BY m.ValidStartTime ASC;