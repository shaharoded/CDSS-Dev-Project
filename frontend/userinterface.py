import tkinter as tk
from tkinter import ttk, messagebox as mb
from PIL import Image, ImageTk
import sys
import os
from datetime import datetime

# Local Code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backend.businesslogic as bs

def add_placeholder(entry, text):
    entry.insert(0, text)
    entry.config(foreground='gray')
    def on_focus_in(event):
        if entry.get() == text:
            entry.delete(0, tk.END)
            entry.config(foreground='black')
    def on_focus_out(event):
        if entry.get() == '':
            entry.insert(0, text)
            entry.config(foreground='gray')
    entry.bind('<FocusIn>', on_focus_in)
    entry.bind('<FocusOut>', on_focus_out)

class CreateToolTip:
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)


    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.top = tk.Toplevel(self.widget)
        self.top.wm_overrideredirect(True)
        self.top.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.top, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def close(self, event=None):
        if hasattr(self, 'top'):
            self.top.destroy()


class CDSSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clinical Decision Support System")
        self.geometry("900x600")
        self.configure(padx=10, pady=10)

        self.entries = {}
        self._setup_ui()

    def clear_fields(self):
        for key, entry in self.entries.items():
            entry.delete(0, tk.END)
    def _setup_ui(self):
        # --- Logo and Title ---
        title_frame = ttk.Frame(self)
        title_frame.grid(row=0, column=0, pady=(0, 10))

        logo_path = os.path.join("images", "logo.png")
        logo_img = Image.open(logo_path).resize((80, 80))
        logo_photo = ImageTk.PhotoImage(logo_img)
        self.logo_photo = logo_photo  # prevent garbage collection

        ttk.Label(title_frame, image=self.logo_photo).grid(row=0, column=0, padx=(0, 10))
        ttk.Label(title_frame, text="Clinical Decision Support System", font=("Helvetica", 18, "bold")).grid(row=0, column=1)

        # --- Input Fields ---
        input_frame = ttk.LabelFrame(self, text="Patient Measurement Entry", padding=10)
        input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        labels = ['Patient ID','First Name', 'Last Name', 'LOINC Code', 'Value', 'Unit', 'Valid Start Time', 'Transaction Time']
        placeholders = {
            'Patient ID': 'e.g., 123456789',
            'First Name': 'e.g., John',
            'Last Name': 'e.g., Doe',
            'LOINC Code': 'e.g., 1234-5',
            'Value': 'e.g., 5.6',
            'Unit': 'e.g., mg/dL',
            'Valid Start Time': 'e.g., 17/5/2018 13:11',
            'Transaction Time': 'e.g., 27/5/2018 10:00'
        }
        tooltips = {
            'Patient ID': 'Required for all operations',
            'First Name': 'Required for all operations',
            'Last Name': 'Required for all operations',
            'LOINC Code': 'Required for Insert / Update / Delete operations',
            'Value': 'Required for Insert / Update operations',
            'Unit': 'Required for Insert operation only',
            'Valid Start Time': 'Required for Insert / Update / Delete operations',
            'Transaction Time': 'Required for Insert operation only'
        }

        for idx, label in enumerate(labels):
            ttk.Label(input_frame, text=label).grid(row=idx, column=0, sticky="w", pady=2)
            entry = ttk.Entry(input_frame, width=40)
            #entry.insert(0, placeholders[label])
            entry.grid(row=idx, column=1, pady=2)
            add_placeholder(entry, placeholders[label])
            CreateToolTip(entry, text=tooltips[label])
            self.entries[label] = entry

        # --- Results Listbox ---
        listbox_frame = ttk.LabelFrame(self, text="Results", padding=10)
        listbox_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.listbox = tk.Listbox(listbox_frame, width=110, height=12, font=("Courier", 10))
        self.listbox.pack(fill="both", expand=True)

        # --- Buttons ---
        button_frame = ttk.Frame(self, padding=10)
        button_frame.grid(row=3, column=0, pady=10, sticky="w")

        ttk.Button(button_frame, text="Insert Measurement", command=self.insert_measurement).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Show History", command=self.show_history).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Update Measurement", command=self.update_measurement).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Delete Measurement", command=self.delete_measurement).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Register Patient", command=self.register_patient).grid(row=0, column=4, padx=5)

    def _get(self, key):
        return self.entries[key].get().strip()

    def register_patient(self):
        try:
            required_fields = ['Patient ID', 'First Name', 'Last Name']
            for field in required_fields:
                value = self._get(field)
                placeholder = f"e.g., {field.split()[0]}"  # matches your placeholders
                if not value or value.startswith("e.g.,"):
                    mb.showerror("Error", f"The field '{field}' is required.")
                    return

            patient_id = self._get('Patient ID')
            first_name = self._get('First Name')
            last_name = self._get('Last Name')

            pr = bs.PatientRecord(patient_id, first_name, last_name)
            exists = pr.check_patient()

            if exists:
                db_first, db_last = exists
                if db_first != first_name or db_last != last_name:
                    mb.showerror("Error",
                                 f"ID {patient_id} already exists under a different name: {db_first} {db_last}")
                    return
                else:
                    mb.showinfo("Info", f"Patient with ID {patient_id} is already registered.")
                    return

            pr.register_patient()
            mb.showinfo("Success", "Patient registered successfully!")

        except Exception as ex:
            mb.showerror("Error", f"Unexpected error: {ex}")

    def insert_measurement(self):
        try:
            required_fields = ['Patient ID', 'First Name', 'Last Name', 'LOINC Code', 'Value', 'Unit',
                               'Valid Start Time', 'Transaction Time']
            for field in required_fields:
                if not self._get(field):
                    mb.showerror("Error", f"The field '{field}' is required.")
                    return

            pr = bs.PatientRecord(self._get('Patient ID'), self._get('First Name'), self._get('Last Name'))
            exists = pr.check_patient()
            if not exists:
                mb.showerror("Error", f"Patient with ID {pr.patient_id} is not registered. Please register first.")
                return

            pr.insert_measurement(
                self._get('LOINC Code'),
                self._get('Value'),
                self._get('Unit'),
                self._get('Valid Start Time'),
                self._get('Transaction Time')
            )
            mb.showinfo("Success", "Measurement inserted successfully!")

        except bs.PatientNotFound:
            mb.showerror("Error", "Patient not found.")
        except Exception as ex:
            mb.showerror("Error", f"Unexpected error: {ex}")

    def show_history(self):
        try:
            first = self._get('First Name')
            last = self._get('Last Name')
            history = bs.PatientRecord.search_history(
                self._get('Patient ID').strip(),
                self._get('First Name'),
                self._get('Last Name')
            )

            self.listbox.delete(0, tk.END)
            if not history:
                self.listbox.insert(tk.END, "No records found.")
                return
            
            header = f"{'LOINC':<12} {'Concept Name':<20} {'Value':<10} {'Unit':<10} {'Valid Start':<18} {'Transaction Time':<18}"
            self.listbox.insert(tk.END, header)
            self.listbox.insert(tk.END, "-" * len(header))

            for row in history:
                loinc, concept, val, unit, vstart, ttime = row[:6]

                def fmt(dtstr):
                    try:
                        dt = datetime.fromisoformat(dtstr)
                        return dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        return dtstr

                self.listbox.insert(
                    tk.END,
                    f"{loinc:<12} {concept:<20} {val:<10} {unit:<10} {fmt(vstart):<18} {fmt(ttime):<18}"
                )

        except bs.PatientNotFound:
            mb.showerror("Error", "Patient not found.")
        except Exception as ex:
            mb.showerror("Error", f"Unexpected error: {ex}")

    def update_measurement(self):
        try:
            bs.PatientRecord.update_measurement(
                self._get('Patient ID'),
                self._get('First Name'),
                self._get('Last Name'),
                self._get('LOINC Code'),
                self._get('Valid Start Time'),
                self._get('Value')
            )
            mb.showinfo("Success", "Measurement updated successfully!")
        except NotImplementedError:
            mb.showerror("Not Implemented", "Update not implemented yet.")
        except bs.PatientNotFound:
            mb.showerror("Error", "Patient not found.")
        except Exception as ex:
            mb.showerror("Error", f"Unexpected error: {ex}")

    def delete_measurement(self): #will need to add id as well
        try:
            bs.PatientRecord.delete_measurement(
                self._get('First Name'),
                self._get('Last Name'),
                self._get('LOINC Code'),
                self._get('Valid Start Time')
            )
            mb.showinfo("Success", "Measurement deleted successfully!")
        except NotImplementedError:
            mb.showerror("Not Implemented", "Delete not implemented yet.")
        except bs.PatientNotFound:
            mb.showerror("Error", "Patient not found.")
        except Exception as ex:
            mb.showerror("Error", f"Unexpected error: {ex}")


if __name__ == '__main__':
    app = CDSSApp()
    app.mainloop()
