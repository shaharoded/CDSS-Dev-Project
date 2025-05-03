-- Purpose: Fetch PatientId by FirstName and LastName

SELECT PatientId
FROM Patients
WHERE PatientId = ? AND FirstName = ? AND LastName = ?
LIMIT 1;