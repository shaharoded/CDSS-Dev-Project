SELECT FirstName, LastName, PatientId
FROM Patients
WHERE FirstName = ? COLLATE NOCASE AND LastName = ? COLLATE NOCASE;
