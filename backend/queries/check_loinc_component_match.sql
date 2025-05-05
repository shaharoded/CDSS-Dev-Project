SELECT 1
FROM Loinc
WHERE LoincNum = ?
  AND Component = ?
LIMIT 1;
