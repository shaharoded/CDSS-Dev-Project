WITH ComponentLoincs AS (
    SELECT LoincNum
    FROM Loinc
    WHERE Component = ?
)
SELECT LoincNum
FROM (
    -- First: prefer one that exists in Measurements
    SELECT cl.LoincNum
    FROM ComponentLoincs cl
    WHERE EXISTS (
        SELECT 1
        FROM Measurements m
        WHERE m.LoincNum = cl.LoincNum
    )
    UNION ALL
    -- Fallback: any from the component list
    SELECT cl.LoincNum
    FROM ComponentLoincs cl
)
LIMIT 1;
