import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Local Code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.businesslogic import PatientRecord, PatientNotFound, LoincCodeNotFound, RecordNotFound

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


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CDSS Patient Interface")
        self.geometry("800x600")

        self.record = PatientRecord()

        # Header Frame
        header_frame = tk.Frame(self)
        header_frame.pack(pady=5)

        # logo
        logo_path = os.path.join("images", "logo.png")
        self.logo = tk.PhotoImage(file=logo_path).subsample(2, 2)  # Resize to 50%

        tk.Label(header_frame, image=self.logo).pack(side="left", padx=10)
        tk.Label(header_frame, text="Patients Management CDSS", font=("Arial", 24, "bold")).pack(side="left")

        # Build pages
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        self._create_patient_search_tab()
        self._create_measure_search_tab()
        self._create_patient_insert_tab()
        self._create_measure_insert_tab()
        self._create_measure_update_tab()
        self._create_measure_delete_tab()

    def _add_labeled_entry(self, parent, label, tooltip_text):
        """
        Add header + tooltip for input cell
        """
        frame = tk.Frame(parent)
        frame.pack(anchor="w", padx=10, pady=2)
        tk.Label(frame, text=label, width=30, anchor="w").pack(side="left")
        entry = tk.Entry(frame, width=40)
        entry.pack(side="left")
        CreateToolTip(entry, tooltip_text)
        return entry

    def _create_patient_search_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Get Patient by Name")

        self.get_first_name = self._add_labeled_entry(tab, "First Name", "• A patient's first name\n• e.g. John")
        self.get_last_name = self._add_labeled_entry(tab, "Last Name", "• A patient's last name\n• e.g. Doe")

        tk.Button(tab, text="Get Patient", command=self.get_patient_by_name).pack(pady=10)
        self.get_result = tk.Text(tab, height=10)
        self.get_result.pack()

    def _create_measure_search_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Search History")

        self.search_patient_id = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.search_loinc = self._add_labeled_entry(tab, "LOINC Code (optional)", "• a Valid LOINC code\n• e.g. 2055-2")
        self.search_start = self._add_labeled_entry(tab, "Start Date/Time (optional)", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")
        self.search_end = self._add_labeled_entry(tab, "End Date/Time (optional)", "• Date/time format\n• e.g. 02/01/2024 23:59 or just 02/01/2024")
        self.search_snapshot = self._add_labeled_entry(tab, "Snapshot Date/Time (optional)", "• Used to show results relative to a past DB snapshot\n• Date/time format\n• e.g. 03/01/2024 00:00 or just 03/01/2024\n• If empty, will automatically use the current DB")

        tk.Button(tab, text="Search", command=self.search_history).pack(pady=10)
        self.search_result = tk.Text(tab, height=15)
        self.search_result.pack()

    def _create_patient_insert_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Insert Patient")

        self.update_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.update_first_name = self._add_labeled_entry(tab, "First Name", "• A patient's first name\n• e.g. John")
        self.update_last_name = self._add_labeled_entry(tab, "Last Name", "• A patient's last name\n• e.g. Doe")

        tk.Button(tab, text="Insert Patient", command=self.insert_measurement).pack(pady=10)
        self.update_result = tk.Text(tab, height=5)
        self.update_result.pack()

    def _create_measure_insert_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Insert Measurement")

        self.update_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.update_loinc = self._add_labeled_entry(tab, "LOINC Code", "• A valid LOINC code\n• e.g. 2055-2")
        self.update_time = self._add_labeled_entry(tab, "Valid Start Time", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")
        self.update_value = self._add_labeled_entry(tab, "New Value", "• Numeric or textual value\n• e.g. 12.5")
        self.update_transaction_time = self._add_labeled_entry(tab, "Transaction Time (Optional)", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024\n• Allows to create retro updates, as if created in past time\n• If empty, will automatically use current date-time")

        tk.Button(tab, text="Insert Measurement", command=self.insert_measurement).pack(pady=10)
        self.update_result = tk.Text(tab, height=5)
        self.update_result.pack()

    def _create_measure_update_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Update Measurement")

        self.update_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.update_loinc = self._add_labeled_entry(tab, "LOINC Code", "• A valid LOINC code\n• e.g. 2055-2")
        self.update_time = self._add_labeled_entry(tab, "Valid Start Time", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")
        self.update_value = self._add_labeled_entry(tab, "New Value", "• Numeric or textual value\n• e.g. 12.5")
        self.update_transaction_time = self._add_labeled_entry(tab, "Transaction Time (Optional)", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024\n• Allows to create retro updates, as if created in past time\n• If empty, will automatically use current date-time")


        tk.Button(tab, text="Update Measurement", command=self.update_measurement).pack(pady=10)
        self.update_result = tk.Text(tab, height=5)
        self.update_result.pack()

    def _create_measure_delete_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Delete Measurement")

        self.delete_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.delete_loinc = self._add_labeled_entry(tab, "LOINC Code", "• A valid LOINC code\n• e.g. 2055-2")
        self.delete_time = self._add_labeled_entry(tab, "Valid Start Time", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")

        tk.Button(tab, text="Delete Measurement", command=self.delete_measurement).pack(pady=10)
        self.delete_result = tk.Text(tab, height=5)
        self.delete_result.pack()

    def get_patient_by_name(self):
        first = self.get_first_name.get()
        last = self.get_last_name.get()
        
        try:
            results = self.record.get_patient_by_name(first, last)
            self.get_result.delete("1.0", tk.END)
            for row in results:
                self.get_result.insert(tk.END, f"ID: {row[0]}, First: {row[1]}, Last: {row[2]}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_history(self):
        pid = self.search_patient_id.get()
        loinc = self.search_loinc.get()
        start = self.search_start.get()
        end = self.search_end.get()
        snap = self.search_snapshot.get()
        try:
            results = self.record.search_history(pid, snapshot_date=snap or None, loinc_num=loinc or None, start=start or None, end=end or None)
            self.search_result.delete("1.0", tk.END)
            for row in results:
                self.search_result.insert(tk.END, f"{row}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def insert_patient(self):
        try:
            self.record.register_patient(
                self.update_pid.get(),
                self.update_first_name.get(),
                self.update_last_name.get()
            )
            messagebox.showinfo("Success", "New patient inserted.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def insert_measurement(self):
        try:
            self.record.insert_measurement(
                self.update_pid.get(),
                self.update_loinc.get(),
                self.update_time.get(),
                self.update_value.get(),
                self.update_transaction_time.get()
            )
            messagebox.showinfo("Success", "Measurement inserted.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_measurement(self):
        try:
            self.record.update_measurement(
                self.update_pid.get(),
                self.update_loinc.get(),
                self.update_time.get(),
                self.update_value.get(),
                self.update_transaction_time.get()
            )
            messagebox.showinfo("Success", "Measurement updated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_measurement(self):
        try:
            self.record.delete_measurement(
                self.delete_pid.get(),
                self.delete_loinc.get(),
                self.delete_time.get()
            )
            messagebox.showinfo("Success", "Measurement deleted.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == '__main__':
    app = Application()
    app.mainloop()