# Training Attendance Processing System

## Overview

The Training Attendance Processing System is a Python utility designed to automatically process training attendance data from Microsoft Teams and correlate it with participant registration records. The script matches attendees who participated in a training session with registered participants and marks them in the registration database.

## Purpose

This tool automates the workflow of:
1. Parsing Teams attendance reports or session roster files (CSV, TSV, or XLSX formats)
2. Filtering participants who met the minimum 30-minute attendance threshold
3. Matching attendees to registered participants using intelligent name normalization with full-name matching and backup initial+last name matching
4. Updating the registration file to mark participants who attended

## System Requirements

- Python 3.6 or higher
- `openpyxl` (optional, only needed for .xlsx file support)
- Standard library: `argparse`, `re`, `csv`, `os`

## Installation

1. Clone or download the repository
2. Ensure Python 3.6+ is installed on your system
3. Install required packages:
   ```bash
   pip install openpyxl flask
   ```
   - `openpyxl` is required to read/write .xlsx files
   - `flask` is required for the web interface

4. For GUI support (desktop only):
   - **Linux:** Most distributions include tkinter. If not, install it:
     ```bash
     sudo apt-get install python3-tk
     ```
   - **Windows:** tkinter is included with Python
   - **macOS:** tkinter is included with Python

## Input Files

### File 1: Attendance Report

**Formats Supported:** 
- The script accepts two input files in CSV, TSV, or XLSX formats:


**Required Columns:**
- `Name` - Participant name (required)
- `Duration` or similar - Attendance duration (optional; if missing, all listed participants are considered attendees)

**Name Format Support:**
- "First Last" (e.g., "Nicholas Lehman")
- "Last, First" (e.g., "Lehman, Nicholas")
- Mixed case handled automatically

**Duration Format Parsing:**
The script intelligently parses various duration formats:
- **"Xh Ym Zs"** format: `1h 7m 42s` → converted to minutes (67.7 min)
- **"Xh Ym"** format: `1h 7m` → 67 minutes
- **"MM:SS"** format: `67:42` → converted to minutes (67.7 min)
- **"X min"** format: `67 min` → 67 minutes
- **Numeric only:** `67.7` or `67` → interpreted as minutes

**Minimum Attendance Threshold:** Only participants with ≥ 30 minutes duration are considered valid attendees.

### File 2: Registration/Roster File

**Formats Supported:** The script accepts two input files in CSV, TSV, or XLSX formats:


**Required Columns:**
- `Name` - Participant name (required)
- `Score` - Completion score column (required)
- `Part1` - Participation marker column (required; this is where attendance is recorded)

**Expected Structure:**
The file should contain a header row with at least the columns above. The script scans for a header row containing both "Name" and "Score" columns.

## Name Matching Logic

### Challenge

The attendance report and registration file may list names in different formats:
- **Attendance Report:** First Name First (e.g., "Nicholas Lehman")
- **Registration File:** Last Name First (e.g., "Lehman, Nicholas")
- **Case variations:** "nicholas lehman", "NICHOLAS LEHMAN", "nicholas lehman"
- **Extra whitespace:** "Nicholas  Lehman" (double spaces)
- **Nicknames:** "Nick Lehman" vs "Nicholas Lehman"
- **Duplicates:** "Bruce Smith" vs "Bryce Smith" (same initial and last name)
- **Suffixes:** "James Strydom Jr" vs "James Strydom"
- **Middle names:** "James M Strydom" vs "James Strydom"
- **Compound last names:** "Maxime Otali" vs "Otali Ondimba"

### Solution: Enhanced Full Name Matching with Backup

#### Primary Matching: Full Name Normalization
Names are normalized to a standardized "first last" format (lowercased) for exact matching. This distinguishes individuals with the same first initial and last name. The normalization process includes:
- Removing suffixes (Jr., Sr., III, etc.)
- Removing one-letter middle names (initials)
- Handling compound last names by using the primary last name component

**Parsing Logic:**
- **"First Last" format:** Convert to "first last" lowercase, removing suffixes and one-letter middle names
  - "Nicholas Lehman" → "nicholas lehman"
  - "Nick Lehman" → "nick lehman"
  - "James M Strydom Jr" → "james strydom"
- **"Last, First" format:** Reorder to "first last" lowercase, removing suffixes and one-letter middle names
  - "Lehman, Nicholas" → "nicholas lehman"
  - "Lehman, Nick" → "nick lehman"
  - "Strydom Jr, James M" → "james strydom"

#### Backup Matching: First Initial + Last Name
If no exact full-name match is found, the script falls back to matching on first initial + last name. This handles cases where attendance reports use abbreviated names.

**Backup Parsing Logic:**
- Extract first letter of first name + full last name
  - "Nicholas Lehman" → `("n", "lehman")`
  - "B. Smith" → `("b", "smith")`

#### Additional Fallback: Last Name Containment
For complex name variations, especially with compound last names, the script includes an additional fallback where the primary last name from the registration is checked against the full attendance name string.

**Example Matching:**
| Attendance | Registration | Match? | Reason |
|-----------|--------------|--------|--------|
| Nicholas Lehman | Lehman, Nicholas | ✓ Yes | Primary: Both → "nicholas lehman" |
| Bryce Smith | Smith, Bryce | ✓ Yes | Primary: Both → "bryce smith" |
| B. Smith | Smith, Bruce | ✓ Yes | Primary fails ("b. smith" ≠ "bruce smith"), Backup: ("b", "smith") |
| jim jones | JONES, JIM | ✓ Yes | Primary: Both → "jim jones" |
| Pena Murillo, Nestor | Nestor Pena Murillo | ✓ Yes | Primary: Both → "nestor pena murillo" |
| James M Strydom Jr | Strydom, James | ✓ Yes | Primary: Both → "james strydom" (suffixes and middle initials removed) |
| Maxime Otali Ondimba | Otali Ondimba, Maxime | ✓ Yes | Primary: Both → "maxime otali" (compound last name truncated), Fallback: "otali" in "maxime otali ondimba" |

**Important Notes:**
- **Primary Priority:** Exact full-name matches are preferred over backup matches
- **Duplicate Handling:** Individuals with the same first initial and last name (e.g., Bruce Smith and Bryce Smith) are distinguished by full name
- **Nickname Tolerance:** Backup matching works for abbreviated first names (e.g., "B. Smith" matches "Bruce Smith")
- **Name Order Independence:** Works regardless of "First Last" or "Last, First" format
- **Whitespace Tolerance:** Extra whitespace is automatically handled
- **Suffix Removal:** Common suffixes like Jr., Sr., III, IV, etc. are removed
- **Middle Name Handling:** One-letter middle names (initials) are omitted to improve matching
- **Compound Last Names:** For names with multiple last name components, matching focuses on the primary last name to handle variations

## Output File

### Updated Registration (`registered_scored.xlsx`)

**Format:** Excel spreadsheet (.xlsx)

**Content:** Copy of the registration file with the `Part1` column updated

**Part1 Column Updates:**
- `1` for participants matching in the attendance file with ≥ 30 minutes duration
- `0` for participants not in the attendance file or with < 30 minutes duration

**Preserved Content:**
- All other columns remain unchanged
- File structure is preserved
- Only the `Part1` column (participation marker) is modified

## Usage

### Web Interface (Recommended for All Users)

For the most user-friendly experience, use the web interface that works in any environment:

```bash
python web_gui.py
```

**Features:**
- **Browser-based GUI**: Works on any device with a web browser
- **Drag & Drop File Upload**: Simply drag files into the upload areas
- **Real-time Progress**: See analysis progress as it happens
- **Download Results**: Download the processed file directly from your browser
- **No Installation Required**: Works in headless environments (servers, containers)

**How to Use:**
1. Run `python web_gui.py`
2. Open your browser to `http://localhost:5000` (opens automatically)
3. Upload your attendance report and registration file
4. Click "Analyze Attendance"
5. Download the results when complete

### GUI Mode (Desktop Only)

For desktop users, a native GUI application is available:

```bash
python gui.py
```

**Requirements:** Requires a graphical desktop environment (Windows, macOS, or Linux with X11)

### Command Line Mode

For advanced users and automation, use the command-line interface:

#### Basic Usage

```bash
python script.py <attendance_file> <registered_file>
```

**Example:**
```bash
python script.py Teams-Attendance-2026-04-08.csv Session-Roster.csv
```

This generates:
- `registered_scored.xlsx` (default output file)

#### Advanced Usage with Custom Output Path

```bash
python script.py <attendance_file> <registered_file> --output <output_file>
```

**Example:**
```bash
python script.py Teams-Attendance.csv Roster.csv --output results/scored-roster.xlsx
```

## Processing Algorithm

### Step 1: Parse Attendance File
1. Load attendance file (auto-detects CSV/TSV/XLSX and encoding)
2. Find header row containing "Name" column
3. Extract participant names and duration (if available)
4. Parse duration strings into minutes using multiple format parsers
5. Filter out participants with < 30 minutes duration
6. Normalize names using first initial + last name approach
7. Create set of valid attendees

### Step 2: Parse PCL Learn Registration File
1. Load registration file (auto-detects CSV/TSV/XLSX and encoding)
2. Locate header row containing both "Name" and "Score" columns
3. Identify required columns: "Name", "Score", "Part1"
4. Extract participant data and store original row structure

### Step 3: Match Attendees to Registered Participants
1. For each registered participant:
   - Normalize their name to full "first last" format (removing suffixes, one-letter middle names, and truncating compound last names)
   - Check if this normalized name exactly matches any valid attendee's normalized name
   - If no exact match, check if first initial + last name matches any attendee's backup key
   - As a final fallback, check if the primary last name from registration appears in the attendee's normalized name
   - Mark as `attended = True` if match found, `False` otherwise
2. Build correspondence between registered participants and attendance

### Step 4: Update Part1 Column
1. For each registered participant in the registration data:
   - Set `Part1` column to `1` if they attended (matched in attendance file with ≥ 30 min)
   - Set `Part1` column to `0` if they did not attend
2. Preserve all other columns unchanged

### Step 5: Write Updated Registration
1. Write updated registration file with modified `Part1` column
2. Display summary: "X of Y registered attendees marked in Part1"


## File Format Support

The script automatically detects and handles:

### Encoding Support
- **Attendance File:** UTF-16, UTF-8-sig, UTF-8, Latin-1, CP1252 (auto-detected)
- **Registration File:** UTF-16, UTF-8-sig, UTF-8, Latin-1, CP1252 (auto-detected)
- The script tries all encoding+delimiter combinations and selects the configuration with the highest median column count

### File Formats
- **CSV** (Comma-separated values)
- **TSV** (Tab-separated values)  
- **XLSX** (Excel format, requires `openpyxl` package)

### Delimiter Auto-Detection
The script automatically tries both comma and tab delimiters to find the correct configuration.

## Duration Parsing

The script intelligently parses multiple duration formats using regular expressions:

```python
# Supported formats:
"1h 7m 42s"   # Hours, minutes, seconds
"1h 7m"       # Hours, minutes
"7m 42s"      # Minutes, seconds
"67:42"       # Minutes:seconds (MM:SS)
"67 min"      # Just minutes with word
"67.7"        # Decimal minutes
"67"          # Plain number (assumed minutes)
```

## Workflow Example

### Scenario

You conducted a 1-hour training session in Microsoft Teams with 50 registered participants.

1. **Export from Teams:** Download attendance report → `Teams-Attendance-2026-04-08.csv`
2. **Export from LMS:** Download session roster → `Session-Roster.csv`
3. **Run script:**
   ```bash
   python script.py Teams-Attendance-2026-04-08.csv Session-Roster.csv
   ```
4. **Review output:**
   - `registered_scored.csv` - Updated registration with `Part1` column marked for attendees
5. **Upload to LMS:** Bulk import `registered_scored.csv` back into your learning platform

## Best Practices

1. **Backup Original Files:** Always keep copies of original attendance and registration files before processing
2. **Verify File Formats:** Ensure files have the required columns ("Name" for both, "Part1" for registration)
3. **Spot-Check Matches:** Manually verify a few name matches in the output to ensure accuracy
4. **Check Attendance Count:** Review the summary message showing how many participants were marked as attended
5. **Document Process:** Keep records of when and which files were processed for audit trails
6. **Test with Small Dataset:** Before processing large batches, test with a sample session first
7. **Handle Encoding Issues:** If you encounter decoding errors, try converting the file to UTF-8 CSV format before processing

## Limitations and Considerations

1. **Name Matching:** Script uses first initial + last name. Names must have a recognizable last name to match (e.g., "John A" vs "A, John" may not match)
2. **Duplicate Names:** If multiple participants have the same first initial and last name, they will all be marked with the same attendance status
