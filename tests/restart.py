from backend.dataaccess import DataAccess

data = DataAccess()
data.cur.execute("DROP TABLE IF EXISTS Measurements;")
data.cur.execute("DROP TABLE IF EXISTS Patients;")
data.conn.commit()
print("[INFO] Dropped Patients and Measurements tables.")
