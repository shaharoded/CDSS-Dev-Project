import sqlite3

conn = sqlite3.connect('../data/cdss.db')
cur = conn.cursor()
cur.execute("SELECT * FROM Patients;")
rows = cur.fetchall()
for row in rows:
    print(row)
conn.close()
