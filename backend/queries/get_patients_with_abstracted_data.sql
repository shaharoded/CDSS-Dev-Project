-- Purpose: Get all unique patient IDs who have abstracted measurements in a specific time window
-- Used for rule processing to find patients with relevant data during snapshot time
-- Parameters: SnapshotDateTime, StartTimeWindow
-- Returns distinct patient IDs where measurements are active in the time window

SELECT DISTINCT PatientId
FROM AbstractedMeasurements
WHERE StartDateTime <= ?
  AND EndDateTime >= ?;