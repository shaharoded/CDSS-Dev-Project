-- Retrieve the LOINC code for a given component (Name) from the Loinc table

SELECT LoincNum
FROM Loinc
WHERE Component = ?
LIMIT 1;
