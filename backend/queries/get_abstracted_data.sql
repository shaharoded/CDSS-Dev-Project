-- Purpose: Get relevant subset of abstracted measurements for a specific time window
-- Used for rule processing to find patient data active during snapshot time. Will return data for all patients.
-- Parameters: SnapshotDateTime, StartTimeWindow
-- Filters by time window (StartDateTime <= snapshot AND EndDateTime >= start_time)

SELECT PatientId,
       LoincNum,
       ConceptName,
       AbstractedValue,
       StartDateTime,
       EndDateTime
FROM AbstractedMeasurements
WHERE StartDateTime <= ?
  AND EndDateTime >= ?
ORDER BY StartDateTime DESC;