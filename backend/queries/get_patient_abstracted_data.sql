-- Purpose: Get abstracted measurements for a specific patient within a time window
-- Used for rule processing to find patient data active during snapshot time
-- Parameters: PatientId, SnapshotDateTime, StartTimeWindow
-- Filters by patient ID and time window (StartDateTime <= snapshot AND EndDateTime >= start_time)

SELECT PatientId,
       LoincNum as 'LOINC-Code',
       ConceptName as 'Concept Name',
       AbstractedValue as 'Value',
       StartDateTime,
       EndDateTime
FROM AbstractedMeasurements
WHERE PatientId = ?
  AND StartDateTime <= ?
  AND EndDateTime >= ?
ORDER BY StartDateTime DESC;