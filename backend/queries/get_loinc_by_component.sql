-- Purpose: Get all appropriate LOINC code based on a given name. 

SELECT LoincNum
FROM Loinc
WHERE Component = ?
