import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Local Code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.businesslogic import PatientRecord
from datetime import datetime

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

        self.search_first_name = self._add_labeled_entry(tab, "First Name", "• A patient's first name\n• e.g. John")
        self.search_last_name = self._add_labeled_entry(tab, "Last Name", "• A patient's last name\n• e.g. Doe")

        tk.Button(tab, text="Get Patient", command=self.get_patient_by_name).pack(pady=10)
        self.get_result = tk.Text(tab, height=10)
        self.get_result.pack()
        self.get_result.configure(state='disabled')  # make read-only by default

    def _create_measure_search_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Search History")

        self.search_patient_id = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.search_loinc = self._add_labeled_entry(tab, "LOINC Code (optional)", "• a Valid LOINC code\n• e.g. 2055-2")
        self.search_start = self._add_labeled_entry(tab, "Start Date/Time (optional)", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")
        self.search_end = self._add_labeled_entry(tab, "End Date/Time (optional)", "• Date/time format\n• e.g. 02/01/2024 23:59 or just 02/01/2024")
        self.search_snapshot = self._add_labeled_entry(tab, "Snapshot Date/Time (optional)", "• Used to show results relative to a past DB snapshot\n• Date/time format\n• e.g. 03/01/2024 00:00 or just 03/01/2024\n• If empty, will automatically use the current DB")

        tk.Button(tab, text="Search", command=self.search_history).pack(pady=10)
        self.search_result = tk.Text(tab, height=15, width=100)
        self.search_result.pack()
        self.search_result.configure(state='disabled')  # make read-only by default


    def _create_patient_insert_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Insert Patient")

        self.insert_patient_update_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.insert_patient_update_first_name = self._add_labeled_entry(tab, "First Name", "• A patient's first name\n• e.g. John")
        self.insert_patient_update_last_name = self._add_labeled_entry(tab, "Last Name", "• A patient's last name\n• e.g. Doe")

        tk.Button(tab, text="Insert Patient", command=self.insert_patient).pack(pady=10)
        self.create_patient_update_result = tk.Text(tab, height=5)
        self.create_patient_update_result.pack()
        self.create_patient_update_result.configure(state='disabled')  # make read-only by default

    def _create_measure_insert_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Insert Measurement")

        self.insert_measurement_update_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.insert_measurement_update_loinc = self._add_labeled_entry(tab, "LOINC Code", "• A valid LOINC code\n• e.g. 2055-2")
        self.insert_measurement_update_component = self._add_labeled_entry(tab, "Component","Optional measurement name\ne.g. Glucose, Hemoglobin")
        self.insert_measurement_update_time = self._add_labeled_entry(tab, "Valid Start Time", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")
        self.insert_measurement_update_value = self._add_labeled_entry(tab, "New Value", "• Numeric or textual value\n• e.g. 12.5")
        self.insert_measurement_update_unit = self._add_labeled_entry(tab, "Unit", "• Textual unit (for the measurement)\n• e.g. m/g")
        self.insert_measurement_update_transaction_time = self._add_labeled_entry(tab, "Transaction Time (Optional)", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024\n• Allows to create retro updates, as if created in past time\n• If empty, will automatically use current date-time")

        tk.Button(tab, text="Insert Measurement", command=self.insert_measurement).pack(pady=10)
        self.create_measurement_update_result = tk.Text(tab, height=5)
        self.create_measurement_update_result.pack()
        self.create_measurement_update_result.configure(state='disabled')  # make read-only by default


    def _create_measure_update_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Update Measurement")

        self.update_measurement_update_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.update_measurement_update_loinc = self._add_labeled_entry(tab, "LOINC Code", "• A valid LOINC code\n• e.g. 2055-2")
        self.update_measurement_update_component = self._add_labeled_entry(tab, "LOINC Component Name (optional)", "• A valid LOINC component name\n• e.g. Albumin\n• You can filter the db using this field, the LOINC-Code or both")
        self.update_measurement_update_time = self._add_labeled_entry(tab, "Valid Start Time", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")
        self.update_measurement_update_value = self._add_labeled_entry(tab, "New Value", "• Numeric or textual value\n• e.g. 12.5")
        self.update_measurement_update_transaction_time = self._add_labeled_entry(tab, "Transaction Time (Optional)", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024\n• Allows to create retro updates, as if created in past time\n• If empty, will automatically use current date-time")


        tk.Button(tab, text="Update Measurement", command=self.update_measurement).pack(pady=10)
        self.update_measurement_update_result = tk.Text(tab, height=5)
        self.update_measurement_update_result.pack()
        self.update_measurement_update_result.configure(state='disabled')  # make read-only by default


    def _create_measure_delete_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Delete Measurement")

        self.delete_measurement_delete_pid = self._add_labeled_entry(tab, "Patient ID", "• A 9 digit number\n• e.g. 208399845")
        self.delete_measurement_delete_loinc = self._add_labeled_entry(tab, "LOINC Code", "• A valid LOINC code\n• e.g. 2055-2")
        self.delete_measurement_valid_time = self._add_labeled_entry(tab, "Valid Start Time", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024")
        self.delete_measurement_delete_time = self._add_labeled_entry(tab, "Deletion Time (Optional)", "• Date/time format\n• e.g. 01/01/2024 00:00 or just 01/01/2024\n• Allows to delete records with past TransactionDeletionTime\n• If empty, will automatically use current date-time")

        tk.Button(tab, text="Delete Measurement", command=self.delete_measurement).pack(pady=10)
        self.delete_measurement_delete_result = tk.Text(tab, height=5)
        self.delete_measurement_delete_result.pack()
        self.delete_measurement_delete_result.configure(state='disabled')  # make read-only by default

    def get_patient_by_name(self):
        first = self.search_first_name.get()
        last = self.search_last_name.get()
        
        try:
            results = self.record.get_patient_by_name(first, last)
            self.get_result.configure(state='normal')  # enable editing
            self.get_result.delete("1.0", tk.END)
            if not results:
                self.get_result.insert(tk.END, "-> No patient found.\n")
                return
            
            self.get_result.insert(tk.END, f"{'ID':<12} {'First Name':<15} {'Last Name':<15}\n")
            self.get_result.insert(tk.END, "-" * 42 + "\n")
            for row in results:
                self.get_result.insert(tk.END, f"{row[0]:<12} {row[1]:<15} {row[2]:<15}\n")
            self.get_result.configure(state='disabled')  # disable editing again
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
            self.search_result.configure(state='normal')  # enable editing
            self.search_result.delete("1.0", tk.END)
            if not results:
                self.search_result.insert(tk.END, "-> No measurement records found for this patient under these conditions.\n")
                return

            self.search_result.insert(tk.END, f"{'LOINC-Code':<10} {'Concept Name':<20} {'Value':<8} {'Unit':<16} {'Start Time':<20} {'Transaction Time':<20}\n")
            self.search_result.insert(tk.END, "-" * 98 + "\n")
            for row in results:
                loinc, concept, value, unit, valid_start, insertion_time = row
                self.search_result.insert(
                    tk.END,
                    f"{loinc:<10} {concept:<20} {value:<8} {unit:<16} {valid_start:<20} {insertion_time:<20}\n"
                )
            self.search_result.configure(state='disabled')  # disable editing again
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def insert_patient(self):
        pid = self.insert_patient_update_pid.get()
        first = self.insert_patient_update_first_name.get()
        last = self.insert_patient_update_last_name.get()

        try:
            self.record.register_patient(pid, first, last)
            self.create_patient_update_result.configure(state='normal')  # enable editing
            self.create_patient_update_result.delete("1.0", tk.END)
            self.create_patient_update_result.insert(tk.END, "-> A new patient record was added to the DB:\n")
            self.create_patient_update_result.insert(tk.END, f"-> PatientId = {pid}, FirstName = {first}, LastName = {last}\n")
            self.create_patient_update_result.configure(state='disabled')  # disable editing again
            messagebox.showinfo("Success", "New patient inserted.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def insert_measurement(self):
        pid = self.insert_measurement_update_pid.get()
        valid_time = self.insert_measurement_update_time.get()
        value = self.insert_measurement_update_value.get()
        unit = self.insert_measurement_update_unit.get()
        loinc_name = self.insert_measurement_update_component.get()
        loinc_code = self.insert_measurement_update_loinc.get()
        transaction_time = self.insert_measurement_update_transaction_time.get()
        if not transaction_time.strip():
            transaction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if loinc_code and loinc_name:
           loinc = f"{loinc_code}: {loinc_name}"
        else:
            if loinc_code:
                loinc = loinc_code
            else:
                loinc = loinc_name
        
        try:
            self.record.insert_measurement(
                pid, valid_time, value, unit, loinc_name, loinc_code, transaction_time
            )
            self.create_measurement_update_result.configure(state='normal')  # enable editing
            self.create_measurement_update_result.delete("1.0", tk.END)
            self.create_measurement_update_result.insert(tk.END, "-> A new patient's measurement record was added to the DB:\n")
            self.create_measurement_update_result.insert(tk.END, f"-> PatientId: {pid}, LOINC: {loinc}, ValidStartTime: {valid_time}\n")
            self.create_measurement_update_result.insert(tk.END, f"-> New Value = {value}\n")
            self.create_measurement_update_result.insert(tk.END, f"-> Effective Date / Time (Transaction time): {transaction_time}\n")
            self.create_measurement_update_result.configure(state='disabled')  # disable editing again
            messagebox.showinfo("Success", "Measurement inserted.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_measurement(self):
        pid = self.update_measurement_update_pid.get()
        valid_time = self.update_measurement_update_time.get()
        new_value = self.update_measurement_update_value.get()
        loinc_name = self.update_measurement_update_component.get()
        loinc_code = self.update_measurement_update_loinc.get()
        transaction_time = self.update_measurement_update_transaction_time.get()
        if not transaction_time.strip():
            transaction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if loinc_code and loinc_name:
           loinc = f"{loinc_code}: {loinc_name}"
        else:
            if loinc_code:
                loinc = loinc_code
            else:
                loinc = loinc_name

        try:
            self.record.update_measurement(
                pid, valid_time, new_value, loinc_name, loinc_code, transaction_time
            )
            self.update_measurement_update_result.configure(state='normal')  # enable editing
            # Input here the message you wish to add when record updates
            # Add the changed 
            self.update_measurement_update_result.delete("1.0", tk.END)
            self.update_measurement_update_result.insert(tk.END, "-> A patient's measurement record was updated in the DB:\n")
            self.update_measurement_update_result.insert(tk.END, f"-> PatientId: {pid}, LOINC: {loinc}, ValidStartTime: {valid_time}\n")
            self.update_measurement_update_result.insert(tk.END, f"-> New Value = {new_value}\n")
            self.update_measurement_update_result.insert(tk.END, f"-> Effective Date / Time (Transaction time): {transaction_time}\n")
            self.update_measurement_update_result.configure(state='disabled')  # disable editing again
            messagebox.showinfo("Success", "Measurement updated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_measurement(self):
        pid = self.delete_measurement_delete_pid.get()
        loinc_code = self.delete_measurement_delete_loinc.get()
        valid_time = self.delete_measurement_valid_time.get()
        deletion_time = self.delete_measurement_delete_time.get()

        try:
            self.record.delete_measurement(
                self.delete_measurement_delete_pid.get(),
                self.delete_measurement_delete_loinc.get(),
                self.delete_measurement_valid_time.get(),
                self.delete_measurement_delete_time.get()
            )
            self.delete_measurement_delete_result.configure(state='normal')  # enable editing
            self.delete_measurement_delete_result.delete("1.0", tk.END)
            self.delete_measurement_delete_result.insert(tk.END, "-> Patient's record deleted from the DB:\n")
            self.delete_measurement_delete_result.insert(tk.END, f"{'ID':<12} {'Loinc-Code':<10} {'Valid Time':<20} {'Deletion Time':<20}\n")
            self.delete_measurement_delete_result.insert(tk.END, "-" * 42 + "\n")
            self.delete_measurement_delete_result.insert(tk.END, f"{pid:<12} {loinc_code:<10} {valid_time:<20} {deletion_time:<20}\n")
            self.delete_measurement_delete_result.configure(state='disabled')  # disable editing again
            messagebox.showinfo("Success", "Measurement deleted.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == '__main__':
    app = Application()
    app.mainloop()