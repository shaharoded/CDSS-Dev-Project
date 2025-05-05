-- Purpose: Fetch PatientId by FirstName and LastName
-- Might refer to more than 1 patient, but will return the 1st PatientId that match the criteria

SELECT PatientId
FROM Patients
WHERE FirstName = ? AND LastName = ?
LIMIT 1;