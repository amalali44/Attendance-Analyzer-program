import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import sys
from pathlib import Path

# Import the core functions from script.py
from script import load_attendance, load_registered, get_backup_key


class AttendanceAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Training Attendance Analyzer")
        self.root.geometry("700x700")
        self.root.resizable(True, True)
        
        self.attendance_file = tk.StringVar(value="")
        self.registered_file = tk.StringVar(value="")
        self.output_file = tk.StringVar(value="registered_scored.xlsx")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the GUI layout."""
        # Title
        title_label = tk.Label(
            self.root,
            text="Training Attendance Analyzer",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Attendance File Section
        attendance_frame = tk.LabelFrame(
            self.root,
            text="Step 1: Select Attendance Report",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        attendance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        attendance_display = tk.Label(
            attendance_frame,
            textvariable=self.attendance_file,
            wraplength=500,
            justify=tk.LEFT,
            fg="pink",
            font=("Arial", 9)
        )
        attendance_display.pack(fill=tk.X, pady=5)
        
        tk.Button(
            attendance_frame,
            text="Browse Attendance File (CSV/XLSX)",
            command=self.select_attendance_file
        ).pack(fill=tk.X)
        
        # Registered File Section
        registered_frame = tk.LabelFrame(
            self.root,
            text="Step 2: Select Registration File",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        registered_frame.pack(fill=tk.X, padx=10, pady=5)
        
        registered_display = tk.Label(
            registered_frame,
            textvariable=self.registered_file,
            wraplength=500,
            justify=tk.LEFT,
            fg="pink",
            font=("Arial", 9)
        )
        registered_display.pack(fill=tk.X, pady=5)
        
        tk.Button(
            registered_frame,
            text="Browse Registration File (CSV/XLSX)",
            command=self.select_registered_file
        ).pack(fill=tk.X)
        
        # Output File Section
        output_frame = tk.LabelFrame(
            self.root,
            text="Step 3: Output File Location (Optional)",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        output_display = tk.Label(
            output_frame,
            textvariable=self.output_file,
            wraplength=500,
            justify=tk.LEFT,
            fg="pink",
            font=("Arial", 9)
        )
        output_display.pack(fill=tk.X, pady=5)
        
        tk.Button(
            output_frame,
            text="Browse Output Location",
            command=self.select_output_file
        ).pack(fill=tk.X)
        
        # Run Button
        tk.Button(
            self.root,
            text="Analyze Attendance",
            command=self.run_analysis,
            bg="green",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=10
        ).pack(fill=tk.X, padx=10, pady=10)
        
        # Output Log
        log_frame = tk.LabelFrame(
            self.root,
            text="Output Log",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_log = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            font=("Arial", 9),
            state=tk.DISABLED
        )
        self.output_log.pack(fill=tk.BOTH, expand=True)
    
    def select_attendance_file(self):
        """Open file dialog to select attendance file."""
        file_path = filedialog.askopenfilename(
            title="Select Attendance Report",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("TSV files", "*.tsv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.attendance_file.set(file_path)
            self.log_message(f"✓ Attendance file selected: {os.path.basename(file_path)}")
    
    def select_registered_file(self):
        """Open file dialog to select registered file."""
        file_path = filedialog.askopenfilename(
            title="Select Registration File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("TSV files", "*.tsv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.registered_file.set(file_path)
            self.log_message(f"✓ Registration file selected: {os.path.basename(file_path)}")
    
    def select_output_file(self):
        """Open file dialog to select output file location."""
        file_path = filedialog.asksaveasfilename(
            title="Save Output File As",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.output_file.set(file_path)
            self.log_message(f"✓ Output file location set: {os.path.basename(file_path)}")
    
    def log_message(self, message):
        """Add a message to the output log."""
        self.output_log.config(state=tk.NORMAL)
        self.output_log.insert(tk.END, message + "\n")
        self.output_log.see(tk.END)  # Auto-scroll to bottom
        self.output_log.config(state=tk.DISABLED)
        self.root.update()  # Force UI update
    
    def run_analysis(self):
        """Run the attendance analysis."""
        # Validate inputs
        if not self.attendance_file.get():
            messagebox.showerror("Error", "Please select an attendance file.")
            return
        
        if not self.registered_file.get():
            messagebox.showerror("Error", "Please select a registration file.")
            return
        
        attendance_path = self.attendance_file.get()
        registered_path = self.registered_file.get()
        output_path = self.output_file.get()
        
        if not os.path.exists(attendance_path):
            messagebox.showerror("Error", f"Attendance file not found: {attendance_path}")
            return
        
        if not os.path.exists(registered_path):
            messagebox.showerror("Error", f"Registration file not found: {registered_path}")
            return
        
        self.log_message("\n" + "="*60)
        self.log_message("Starting analysis...")
        self.log_message("="*60)
        
        try:
            import csv
            import openpyxl
            
            # Load attendance data
            self.log_message("\n[1/4] Loading attendance report...")
            valid_attendees = load_attendance(attendance_path)
            self.log_message(f"      Found {len(valid_attendees)} valid attendees")
            
            # Load registration data
            self.log_message("\n[2/4] Loading registration file...")
            registered_data, part1_col, part1_idx, headers, rows, header_row = load_registered(registered_path)
            self.log_message(f"      Found {len(registered_data)} registered participants")
            
            # Match attendees
            self.log_message("\n[3/4] Matching attendees to registrations...")
            matched_count = 0
            for item in registered_data:
                item_backup = get_backup_key(item["normalized_name"])
                for attendee in valid_attendees:
                    attendee_backup = get_backup_key(attendee["normalized_name"])
                    if (item["normalized_name"] == attendee["normalized_name"] or 
                        item_backup == attendee_backup or 
                        item_backup[1] in attendee["normalized_name"]):
                        item["attended"] = True
                        matched_count += 1
                        break
            self.log_message(f"      Matched {matched_count} participants")
            
            # Update Part1 column
            self.log_message("\n[4/4] Updating registration file...")
            for item_idx, item in enumerate(registered_data):
                row_idx = header_row + 1 + item_idx
                if row_idx < len(rows):
                    while len(rows[row_idx]) <= part1_idx:
                        rows[row_idx].append('')
                    rows[row_idx][part1_idx] = 1 if item["attended"] else 0
            
            # Write output file
            if output_path.lower().endswith('.xlsx'):
                wb = openpyxl.Workbook()
                ws = wb.active
                for row in rows:
                    ws.append(row)
                wb.save(output_path)
                self.log_message(f"      Saved as Excel file")
            else:
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerows(rows)
                self.log_message(f"      Saved as CSV file")
            
            attended_count = sum(1 for item in registered_data if item["attended"])
            
            self.log_message("\n" + "="*60)
            self.log_message("✓ ANALYSIS COMPLETE")
            self.log_message("="*60)
            self.log_message(f"\nResults:")
            self.log_message(f"  • Attendees marked: {attended_count} of {len(registered_data)}")
            self.log_message(f"  • Output file: {output_path}")
            self.log_message(f"\n✓ File saved successfully!")
            
            messagebox.showinfo(
                "Success",
                f"Analysis complete!\n\n"
                f"Marked {attended_count} of {len(registered_data)} attendees.\n\n"
                f"Output saved to:\n{output_path}"
            )
        
        except ImportError as e:
            self.log_message(f"\n✗ Error: {str(e)}")
            messagebox.showerror(
                "Import Error",
                f"Missing required library:\n{str(e)}\n\n"
                f"Please install it using:\npip install openpyxl"
            )
        except Exception as e:
            self.log_message(f"\n✗ Error: {str(e)}")
            messagebox.showerror(
                "Error",
                f"An error occurred:\n\n{str(e)}"
            )


def run_command_line_interface():
    """Run a simple command-line interface for file selection."""
    print("=" * 60)
    print("Training Attendance Analyzer - Command Line Mode")
    print("=" * 60)
    print("")
    
    # Get attendance file
    attendance_file = input("Enter path to attendance report (CSV/XLSX): ").strip()
    if not attendance_file:
        print("No attendance file provided. Exiting.")
        return
    
    if not os.path.exists(attendance_file):
        print(f"Error: Attendance file not found: {attendance_file}")
        return
    
    # Get registration file
    registered_file = input("Enter path to registration file (CSV/XLSX): ").strip()
    if not registered_file:
        print("No registration file provided. Exiting.")
        return
    
    if not os.path.exists(registered_file):
        print(f"Error: Registration file not found: {registered_file}")
        return
    
    # Get output file (optional)
    output_file = input("Enter output file path (default: registered_scored.xlsx): ").strip()
    if not output_file:
        output_file = "registered_scored.xlsx"
    
    print("")
    print("Starting analysis...")
    print("-" * 40)
    
    try:
        import csv
        import openpyxl
        
        # Load attendance data
        print("Loading attendance report...")
        valid_attendees = load_attendance(attendance_file)
        print(f"  Found {len(valid_attendees)} valid attendees")
        
        # Load registration data
        print("Loading registration file...")
        registered_data, part1_col, part1_idx, headers, rows, header_row = load_registered(registered_file)
        print(f"  Found {len(registered_data)} registered participants")
        
        # Match attendees
        print("Matching attendees to registrations...")
        matched_count = 0
        for item in registered_data:
            item_backup = get_backup_key(item["normalized_name"])
            for attendee in valid_attendees:
                attendee_backup = get_backup_key(attendee["normalized_name"])
                if (item["normalized_name"] == attendee["normalized_name"] or 
                    item_backup == attendee_backup or 
                    item_backup[1] in attendee["normalized_name"]):
                    item["attended"] = True
                    matched_count += 1
                    break
        print(f"  Matched {matched_count} participants")
        
        # Update Part1 column
        print("Updating registration file...")
        for item_idx, item in enumerate(registered_data):
            row_idx = header_row + 1 + item_idx
            if row_idx < len(rows):
                while len(rows[row_idx]) <= part1_idx:
                    rows[row_idx].append('')
                rows[row_idx][part1_idx] = 1 if item["attended"] else 0
        
        # Write output file
        if output_file.lower().endswith('.xlsx'):
            wb = openpyxl.Workbook()
            ws = wb.active
            for row in rows:
                ws.append(row)
            wb.save(output_file)
            print("  Saved as Excel file")
        else:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerows(rows)
            print("  Saved as CSV file")
        
        attended_count = sum(1 for item in registered_data if item["attended"])
        
        print("")
        print("=" * 60)
        print("✓ ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"\nResults:")
        print(f"  • Attendees marked: {attended_count} of {len(registered_data)}")
        print(f"  • Output file: {output_file}")
        print(f"\n✓ File saved successfully!")
        
    except ImportError as e:
        print(f"Error: Missing required library: {e}")
        print("Please install it using: pip install openpyxl")
    except Exception as e:
        print(f"Error: {e}")


def main():
    # Check if GUI is available
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the window temporarily
        root.destroy()   # Destroy it to test if tkinter works
        gui_available = True
    except tk.TclError as e:
        if "no display" in str(e).lower():
            gui_available = False
        else:
            raise  # Re-raise other tkinter errors
    
    if gui_available:
        # GUI mode
        root = tk.Tk()
        app = AttendanceAnalyzerGUI(root)
        root.mainloop()
    else:
        # Web interface
        from web_gui import main as web_main
        web_main()

if __name__ == "__main__":
    main()
