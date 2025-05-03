import sqlite3

# Connect to the database
conn = sqlite3.connect('../data/cdss.db')
cur = conn.cursor()

# Replace 'your_table_name' with the table you want to print (e.g., 'Patients' or 'Measurements')
table_name = 'Patients'

# Execute the SELECT query
cur.execute(f"SELECT * FROM {table_name}")

# Fetch all rows
rows = cur.fetchall()

# Print the column names
column_names = [description[0] for description in cur.description]
print(" | ".join(column_names))

# Print each row
for row in rows:
    print(" | ".join(str(item) for item in row))

# Close the connection
conn.close()
