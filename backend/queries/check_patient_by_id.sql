-- Purpose: Fetch Patient Name by their unique PatientId

SELECT FirstName, LastName FROM Patients WHERE PatientId = ? LIMIT 1;
