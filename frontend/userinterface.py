import tkinter as tk
from tkinter import ttk, messagebox as mb
import backend.businesslogic as bs

# GUI Initialization
app = tk.Tk()
app.title("Clinical Decision Support System")
app.geometry("800x400")
app.configure(padx=10, pady=10)

# Input Frame
input_frame = ttk.LabelFrame(app, text="Patient Measurement Entry", padding=10)
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

# Inputs
labels = ['First Name', 'Last Name', 'LOINC Code', 'Value', 'Unit', 'Valid Start Time', 'Transaction Time']
entries = {}

for idx, label in enumerate(labels):
    ttk.Label(input_frame, text=label).grid(row=idx, column=0, sticky="w", pady=2)
    entry = ttk.Entry(input_frame, width=30)
    entry.grid(row=idx, column=1, pady=2)
    entries[label] = entry

# Listbox Frame
listbox_frame = ttk.LabelFrame(app, text="Results", padding=10)
listbox_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

listbox = tk.Listbox(listbox_frame, width=100, height=10)
listbox.pack(fill="both", expand=True)

# Functions
def insert_measurement():
    try:
        pr = bs.PatientRecord(entries['First Name'].get(), entries['Last Name'].get())
        pr.insert_measurement(
            entries['LOINC Code'].get(),
            entries['Value'].get(),
            entries['Unit'].get(),
            entries['Valid Start Time'].get(),
            entries['Transaction Time'].get()
        )
        mb.showinfo("Success", "Measurement inserted successfully!")
    except bs.PatientNotFound:
        mb.showerror("Error", "Patient not found.")
    except Exception as ex:
        mb.showerror("Error", f"Unexpected error: {ex}")

def show_history():
    try:
        first_name = entries['First Name'].get()
        last_name = entries['Last Name'].get()
        history = bs.PatientRecord.search_history(first_name, last_name)

        listbox.delete(0, tk.END)
        for record in history:
            listbox.insert(tk.END, record)

    except bs.PatientNotFound:
        mb.showerror("Error", "Patient not found.")
    except Exception as ex:
        mb.showerror("Error", f"Unexpected error: {ex}")

# Buttons Frame
button_frame = ttk.Frame(app, padding=10)
button_frame.grid(row=2, column=0, pady=10)

ttk.Button(button_frame, text="Insert Measurement", command=insert_measurement).grid(row=0, column=0, padx=5)
ttk.Button(button_frame, text="Show History", command=show_history).grid(row=0, column=1, padx=5)

app.mainloop()
