# Training Attendance Processing System

## Overview

The Training Attendance Processing System is a Python utility designed to automatically process Microsoft Teams meeting attendance reports and correlate them with participant registration records. The script identifies attendees with insufficient participation time and updates their completion scores in a registration database.

## Purpose

This tool automates the workflow of:
1. Parsing Teams meeting attendance data
2. Identifying participants who attended less than 30 minutes
3. Flagging short attendees in the attendance report
4. Updating registration scores for participants who met the minimum attendance requirement

## System Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library: `argparse`, `re`, `csv`)

## Installation

1. Clone or download the repository
2. Ensure Python 3.6+ is installed on your system
3. No additional packages need to be installed

## Input Files

### File 1: Teams Attendance Report (`.csv`)

**Format:** Tab-separated values (TSV), UTF-16 encoded

**Source:** Exported from Microsoft Teams meeting details → "Download attendance report"

**Structure:**
```
Row 0-6:     Summary section (meeting title, dates, durations, etc.)
Row 7:       Blank separator
Row 8:       Section header "2. Participants"
Row 9+:      Participant attendance records
```

**Columns (starting at Row 9):**
| Column | Description | Example |
|--------|-------------|---------|
| 0 | Full Name | "Aban Iqbal" |
| 1 | Join Time | "4/08/26, 10:44:30 AM" |
| 2 | Leave Time | "4/08/26, 11:52:13 AM" |
| 3 | In-Meeting Duration | "1h 7m 42s" |
| 4 | Email | "aiqbal@pcl.com" |
| 5 | Email (duplicate) | "aiqbal@pcl.com" |
| 6 | Role | "Attendee" |

**Duration Format Parsing:**
The script intelligently parses various duration formats:
- **"Xh Ym Zs"** format: `1h 7m 42s` → converted to minutes (67.7 min)
- **"MM:SS"** format: `67:42` → converted to minutes (67.7 min)
- **"X min"** format: `67 min` → 67 minutes
- **Numeric only:** `67.7` → 67.7 minutes

**Short Attendance Threshold:** Participants with less than 30 minutes are flagged as "SHORT"

### File 2: Registration/Session Roster (`.csv`)

**Format:** Comma-separated values (CSV), UTF-8 encoded

**Source:** Learning Management System (LMS) bulk update file

**Structure:**
```
Rows 0-5:    Instructions and metadata (do not modify)
Row 6:       Column headers
Row 7+:      Participant records
```

**Header Row (Row 6):**
| Column | Header | Purpose | Read-Only |
|--------|--------|---------|-----------|
| 0 | Name [Do not update data] | Participant full name | Yes |
| 1 | Locator [Do not update data] | LMS identifier | Yes |
| 2 | User ID [Do not update data] | LMS user ID | Yes |
| 3 | Score | Completion score (0 or 1) | **No** |
| 4 | Pass | Pass/fail flag (1 or 0) | No |
| 5 | Part1 | Partial completion (1 or 0) | No |

**Initial Score Value:** All participants typically start with a score of `0`

## Name Matching Logic

### Challenge

The attendance report and registration file may list names in different formats:
- **Attendance Report:** First Name First (e.g., "Aban Iqbal")
- **Registration File:** Last Name First (e.g., "Iqbal, Aban")
- **Case variations:** "ABAN IQBAL", "aban iqbal", "Aban iqbal"
- **Extra whitespace:** "Aban  Iqbal" (double spaces)

### Solution: Normalized Name Matching

The script implements a normalization function to handle these variations:

```python
def normalize_name(name):
    # 1. Convert to lowercase
    # 2. Strip leading/trailing whitespace
    # 3. Collapse multiple internal whitespaces to single spaces
    # Returns: "aban iqbal" for all name variations above
```

**Example Normalization:**
| Original | Normalized |
|----------|-----------|
| Aban Iqbal | aban iqbal |
| iqbal, aban | iqbal aban |
| ABAN  IQBAL | aban iqbal |
| aban iqbal | aban iqbal |

**Matching Process:**
1. Extract names from both files
2. Normalize each name using the normalization function
3. Create a set of normalized names from attendance report
4. Compare normalized names to identify matches
5. Scores are updated only for matches found

### Important Notes

- **Name Order Independence:** Matches work regardless of whether names are "First Last" or "Last, First" format (after normalization)
- **Case Insensitivity:** All matching is case-insensitive
- **Whitespace Tolerance:** Extra whitespace is automatically handled
- **Exact Match Requirement:** Normalized names must match exactly (no fuzzy matching)

## Output Files

### Output File 1: Highlighted Attendance (`attendance_highlighted.tsv`)

**Format:** Tab-separated values, UTF-8 encoded

**Content:** Copy of the original attendance report with an additional column appended

**New Column (Column 7):** `FLAG`
- Empty for attendees with ≥ 30 minutes participation
- Contains `"SHORT"` for attendees with < 30 minutes participation

**Use Case:** Allows manual review and verification of which participants need follow-up

### Output File 2: Updated Registration (`registered_scored.csv`)

**Format:** Comma-separated values, UTF-8 encoded

**Content:** Copy of the registration file with Score column updated

**Score Updates:**
- `1` for participants matching attendance report AND meeting minimum duration
- `0` for participants not in attendance report OR failing to meet minimum duration

**Preserved Content:**
- Instructions rows (0-5) remain unchanged
- Headers and all other columns remain unchanged
- Only the "Score" column (Column 3) is modified

## Usage

### Basic Usage

```bash
python script.py <attendance_file> <registered_file>
```

**Example:**
```bash
python script.py attendance_report.csv session_roster.csv
```

This generates:
- `attendance_highlighted.tsv` (default output for attendance)
- `registered_scored.csv` (default output for registration)

### Advanced Usage with Custom Output Paths

```bash
python script.py <attendance_file> <registered_file> \
  --attendance-out <output_path> \
  --registered-out <output_path>
```

**Example:**
```bash
python script.py attendance_report.csv session_roster.csv \
  --attendance-out /reports/2026-04-08-attendance.tsv \
  --registered-out /reports/2026-04-08-scores.csv
```

## Processing Algorithm

### Step 1: Parse Attendance Report
1. Load and decode attendance file (handles UTF-16 encoding)
2. Extract participant data starting from Row 9
3. Parse duration strings into minutes
4. Normalize participant names
5. Create attendance data structure with flags for short attendance

### Step 2: Highlight Short Attendees
1. Add "FLAG" column to attendance data
2. Mark each participant as "SHORT" if duration < 30 minutes
3. Write updated attendance report to output file

### Step 3: Parse Registration File
1. Load and decode registration file (handles CSV format)
2. Locate header row (typically Row 6)
3. Identify Name and Score columns
4. Extract participant data

### Step 4: Match and Score
1. Create set of normalized names with valid attendance (≥ 30 minutes)
2. For each registered participant:
   - Normalize their name
   - Check if normalized name exists in valid attendance set
   - Set score to `1` if match found, `0` otherwise
3. Update Score column in registration data

### Step 5: Write Results
1. Write updated attendance report
2. Write updated registration file
3. Display confirmation messages

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Could not decode file` | Unsupported encoding | Ensure file is UTF-16 (attendance) or UTF-8 (registration) |
| `File doesn't have enough rows` | Incomplete attendance report | Download fresh report from Teams |
| `Missing required column` | Different file format | Verify correct file was provided |
| `Could not find 'Name' column` | Registration file format changed | Verify file is valid LMS bulk update format |

## File Format Verification

### Verify Attendance Report Format

Open the attendance file in a text editor and confirm:
1. First 8 rows contain summary information
2. Row 8 contains "2. Participants"
3. Row 9 contains first participant (name, join time, etc.)

### Verify Registration File Format

Open the registration file in a text editor and confirm:
1. Rows 0-5 contain instructions (do not delete)
2. Row 6 contains headers: "Name [Do not update data]", "Score", etc.
3. Row 7+ contains participant records

## Technical Details

### Encoding Handling

The script automatically detects and handles:
- **Attendance File:** UTF-16 encoded (Teams export default)
- **Registration File:** UTF-8 encoded (LMS export default)
- **Fallback encodings:** Latin-1 and CP1252 if primary fails

### Delimiter Detection

- **Attendance file:** Tab-separated (TSV)
- **Registration file:** Comma-separated (CSV)
- **Auto-detection:** Script tries multiple delimiters to find correct parsing

### Duration Parsing

The script parses multiple duration formats using regular expressions:

```python
# Supported formats:
"1h 7m 42s"   # Hours, minutes, seconds
"67:42"       # Minutes:seconds
"67 min"      # Just minutes
"67.7"        # Decimal minutes
```

## Workflow Example

### Scenario

You conducted a 1-hour training session in Teams with 50 registered participants.

1. **Export from Teams:** Download attendance report as `Teams-Attendance-2026-04-08.csv`
2. **Export from LMS:** Download session roster as `LMS-SessionRoster.csv`
3. **Run script:**
   ```bash
   python script.py Teams-Attendance-2026-04-08.csv LMS-SessionRoster.csv
   ```
4. **Review results:**
   - `attendance_highlighted.tsv` - See who attended < 30 min (marked "SHORT")
   - `registered_scored.csv` - See updated scores for all participants
5. **Upload to LMS:** Import `registered_scored.csv` back into LMS for bulk score update

## Best Practices

1. **Backup Original Files:** Keep copies of original attendance and registration files before processing
2. **Verify Report Completeness:** Ensure Teams attendance report was downloaded for the entire session (check "Attended participants" count)
3. **Review Flagged Records:** Examine `attendance_highlighted.tsv` to verify which participants were marked as "SHORT"
4. **Spot-Check Matches:** Manually verify a few name matches in `registered_scored.csv` to ensure accuracy
5. **Document Process:** Keep records of when and which files were processed
6. **Test with Small Dataset:** Before processing large batches, test with a sample session

## Limitations and Considerations

1. **Name Matching:** Script relies on exact name normalization. Misspelled or significantly different names may not match (e.g., "John" vs "Jon")
2. **Duplicate Names:** If multiple participants have the same normalized name, all matching names in registration will be scored
3. **Case Sensitivity (Pre-Normalization):** Field names in headers are case-sensitive before normalization
4. **Minimum Duration:** Hard-coded to 30 minutes; cannot be customized without modifying source code
5. **Duration Precision:** Very short or unusual duration formats may not parse correctly

## Support and Troubleshooting

### Debug Information

To troubleshoot issues:
1. Verify input files are correct format (use `file` command on Linux/Mac)
2. Check file encoding: `file -b --mime-encoding <filename>`
3. Review first few rows: `head -10 <filename>`
4. Verify column structure matches documentation above

### Common Scenarios

**Q: Why did a participant's score not update?**
- A: Their name in the registration file may not exactly match (after normalization) the attendance report. Verify spelling matches.

**Q: Why are some people marked "SHORT"?**
- A: They joined/left the meeting within less than 30 minutes total. Review join/leave times in attendance report.

**Q: Can I process multiple sessions at once?**
- A: Currently, the script processes one session at a time. Run separately for each session's files.

## Version History

- **v1.0** (2026-04-22): Initial release
  - Support for Teams attendance reports (UTF-16 TSV format)
  - Support for LMS registration files (UTF-8 CSV format)
  - Normalized name matching (case-insensitive, whitespace-tolerant)
  - Automatic encoding and delimiter detection

## License

[Add your license information here]

## Contact

[Add contact information or support details here]