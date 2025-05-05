import sqlite3

conn = sqlite3.connect('../data/cdss.db')  # adjust the path if needed
cur = conn.cursor()

# Insert John Doe if not exists
cur.execute("""
INSERT INTO Patients (FirstName, LastName)
SELECT 'John', 'Doe'
WHERE NOT EXISTS (
    SELECT 1 FROM Patients WHERE FirstName = 'John' AND LastName = 'Doe'
);
""")

conn.commit()
conn.close()
print("Inserted John Doe (if not already present).")
