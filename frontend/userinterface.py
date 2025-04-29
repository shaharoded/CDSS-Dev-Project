import tkinter as tk
from tkinter import ttk, messagebox as mb
from PIL import Image, ImageTk
import sys
import os
from datetime import datetime

# Local Code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backend.businesslogic as bs

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

        labels = ['First Name', 'Last Name', 'LOINC Code', 'Value', 'Unit', 'Valid Start Time', 'Transaction Time']
        placeholders = {
            'First Name': 'e.g., John',
            'Last Name': 'e.g., Doe',
            'LOINC Code': 'e.g., 1234-5',
            'Value': 'e.g., 5.6',
            'Unit': 'e.g., mg/dL',
            'Valid Start Time': 'e.g., 17/5/2018 13:11',
            'Transaction Time': 'e.g., 27/5/2018 10:00'
        }
        tooltips = {
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
            entry.insert(0, placeholders[label])
            entry.grid(row=idx, column=1, pady=2)
            CreateToolTip(entry, text=tooltips[label])
            self.entries[label] = entry

        # --- Results Listbox ---
        listbox_frame = ttk.LabelFrame(self, text="Results", padding=10)
        listbox_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.listbox = tk.Listbox(listbox_frame, width=110, height=12, font=("Courier", 10))
        self.listbox.pack(fill="both", expand=True)

        # --- Buttons ---
        button_frame = ttk.Frame(self, padding=10)
        button_frame.grid(row=3, column=0, pady=10)

        ttk.Button(button_frame, text="Insert Measurement", command=self.insert_measurement).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Show History", command=self.show_history).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Update Measurement", command=self.update_measurement).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Delete Measurement", command=self.delete_measurement).grid(row=0, column=3, padx=5)

    def _get(self, key):
        return self.entries[key].get().strip()

    def insert_measurement(self):
        try:
            pr = bs.PatientRecord(self._get('First Name'), self._get('Last Name'))
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
            history = bs.PatientRecord.search_history(first, last)

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

    def delete_measurement(self):
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
