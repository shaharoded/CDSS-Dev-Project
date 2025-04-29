-- Purpose: Fetch PatientId by FirstName and LastName

SELECT PatientId
FROM Patients
WHERE FirstName = ? AND LastName = ?
LIMIT 1;