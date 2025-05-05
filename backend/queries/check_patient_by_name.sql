-- Purpose: Fetch All PatientIds by FirstName and LastName
-- Will be used to verify the system ID for a patient if only the name is known.

SELECT PatientId, FirstName, LastName
FROM Patients
WHERE FirstName = ? AND LastName = ?
