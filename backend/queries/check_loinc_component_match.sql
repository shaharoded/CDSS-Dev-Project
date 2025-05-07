
SELECT CASE
           WHEN EXISTS (
               SELECT 1
               FROM Loinc
               WHERE Component = ?
                 AND LoincNum = ?
           )
           THEN 1
           ELSE 0
       END AS MatchResult;
