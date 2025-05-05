-- Retrieve the LOINC code for a given component from the Loinc table
SELECT LoincNum
FROM Loinc
WHERE Component = ?
LIMIT 1;
