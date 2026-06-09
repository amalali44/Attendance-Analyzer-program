import argparse, re, csv, os

def parse_name_parts(name: str):
    """Return normalized full name as "first last" lowercase, or empty string if invalid.

    Handles "First Last" or "Last, First" formats.

    Examples:
      "Nicholas Lehman"      -> "nicholas lehman"
      "Nick Lehman"          -> "nick lehman"
      "Lehman, Nicholas"     -> "nicholas lehman"
      "Pena Murillo, Nestor" -> "nestor pena murillo"
      "B. Smith"             -> "b. smith"
    """
    suffixes = ['jr', 'sr', 'iii', 'iv', 'v', 'vi', 'vii', 'jr.', 'sr.', 'iv.', 'v.', 'vi.']
    
    def clean_parts(parts):
        return [p for p in parts if p.lower() not in suffixes and len(p) > 1]
    
    if not name:
        return ""
    cleaned = re.sub(r"\s+", " ", str(name)).strip()

    if "," in cleaned:
        parts = cleaned.split(",", 1)
        last_parts = clean_parts(parts[0].strip().split())
        first_parts = clean_parts(parts[1].strip().split())
        last = " ".join(last_parts)
        first = " ".join(first_parts)
    else:
        tokens = cleaned.split()
        cleaned_tokens = clean_parts(tokens)
        first = cleaned_tokens[0] if cleaned_tokens else ""
        last = " ".join(cleaned_tokens[1:]) if len(cleaned_tokens) > 1 else ""

    if last:
        last = last.split()[0]
    full = f"{first} {last}".strip().lower()
    return full


def get_backup_key(full_name: str):
    """Return (first_initial, last_name) tuple for backup matching."""
    if not full_name:
        return ("", "")
    parts = full_name.split()
    if not parts:
        return ("", "")
    first = parts[0]
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    initial = first[0] if first else ""
    return (initial, last)





def parse_duration(value):
    """Return duration in minutes, or None if unparseable.

    Supported formats:
      "1h 7m 19s"   (Teams attendance report export)
      "58m 30s"
      "45m"
      "MM:SS"       (simple minutes:seconds)
      "90"          (plain number, assumed minutes)
      "90 min"
    """
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    # "Xh Ym Zs" / "Xh Ym" / "Ym Zs" / "Xh" — Teams export format
    h = m_val = s = 0
    matched = False
    mh = re.search(r"(\d+)\s*h", text, re.I)
    mm = re.search(r"(\d+)\s*m(?!in|s)", text, re.I)  # 'm' but not 'min' or 'ms'
    ms = re.search(r"(\d+)\s*s(?!\w)", text, re.I)
    if mh or mm or ms:
        if mh:
            h = int(mh.group(1))
            matched = True
        if mm:
            m_val = int(mm.group(1))
            matched = True
        if ms:
            s = int(ms.group(1))
            matched = True
        if matched:
            return h * 60 + m_val + s / 60

    # "X min" format
    m_min = re.search(r"(\d+(?:\.\d+)?)\s*min", text, re.I)
    if m_min:
        return float(m_min.group(1))

    # "MM:SS" format — only match if it looks like a short duration (no AM/PM nearby)
    if re.search(r"^\d{1,3}:\d{2}$", text.strip()):
        try:
            parts = text.split(":")
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes + seconds / 60
        except (ValueError, IndexError):
            pass

    # Plain number — assume minutes
    m_num = re.search(r"^(\d+(?:\.\d+)?)$", text.strip())
    if m_num:
        return float(m_num.group(1))

    return None


def find_column(headers, expected):
    lower = expected.lower()
    normalized = [h for h in headers if h]
    exact_match = {h.lower(): h for h in normalized}
    if lower in exact_match:
        return exact_match[lower]
    for h in normalized:
        if lower in h.lower():
            return h
    raise KeyError(f"Missing required column '{expected}'. Available: {headers}")


def load_xlsx(path):
    """Load an xlsx file and return rows as a list of lists of strings."""
    try:
        import openpyxl  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "openpyxl is required to read .xlsx files. Install it with "
            "`pip install openpyxl`."
        ) from exc
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append([("" if cell is None else str(cell).strip()) for cell in row])
    return rows


def load_csv_with_encoding(path):
    """Try to load CSV/TSV with different encodings and delimiters.

    Evaluates ALL encoding+delimiter pairs and picks the one with the highest
    median column count, so a UTF-16 TSV is never mis-parsed as single-column CSV.
    """
    import statistics

    encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    delimiters = [',', '\t']

    best_rows = None
    best_score = 0

    for encoding in encodings:
        try:
            with open(path, 'r', newline='', encoding=encoding) as f:
                file_content = f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue

        for delimiter in delimiters:
            try:
                rows = list(csv.reader(file_content.splitlines(), delimiter=delimiter))
                non_empty = [row for row in rows if any(c.strip() for c in row)]
                if not non_empty:
                    continue
                score = statistics.median(len(row) for row in non_empty)
                if score > best_score:
                    best_score = score
                    best_rows = rows
            except Exception:
                continue

    if best_rows is not None:
        return best_rows
    raise ValueError(f"Could not decode file {path} with any supported encoding/delimiter")


def load_file(path):
    """Load either a .xlsx or a CSV/TSV file and return rows as list of lists of strings."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xlsx', '.xlsm'):
        return load_xlsx(path)
    return load_csv_with_encoding(path)


def find_header_row(rows, required_keywords):
    """
    Scan rows top-to-bottom and return the index of the first row whose cells
    contain ALL of the required keywords (case-insensitive substring match).
    Returns None if no such row is found.
    """
    for i, row in enumerate(rows):
        cells_lower = [c.strip().lower() for c in row if c and c.strip()]
        if all(any(kw in cell for cell in cells_lower) for kw in required_keywords):
            return i
    return None


def load_attendance(path):
    rows = load_file(path)

    # Two supported formats:
    #   1. Teams attendance report  — has columns "Name" and "Duration"
    #   2. SessionRoster / bulk-update file — has "Name [Do not update data]"
    #      with no Duration column; every row in the data section is an attendee.

    # Try Teams attendance format first (requires both name + duration)
    header_row_idx = find_header_row(rows, ["name", "duration"])
    has_duration = True

    if header_row_idx is None:
        # Fall back to roster format (name column only)
        header_row_idx = find_header_row(rows, ["name"])
        has_duration = False

    if header_row_idx is None:
        raise ValueError(
            "Attendance file: could not find a header row containing a 'Name' column.\n"
            "  Expected either a Teams attendance report (Name + Duration columns)\n"
            "  or a SessionRoster export (Name [Do not update data] column)."
        )

    headers = [h.strip() for h in rows[header_row_idx]]

    try:
        name_col = find_column(headers, "name")
    except KeyError as e:
        raise KeyError(f"Attendance file header row (row {header_row_idx}): {e}")

    name_idx = headers.index(name_col)

    if has_duration:
        try:
            duration_col = find_column(headers, "duration")
        except KeyError as e:
            raise KeyError(f"Attendance file header row (row {header_row_idx}): {e}")
        duration_idx = headers.index(duration_col)
    else:
        duration_idx = None
        print("  Note: No 'Duration' column found — treating all rows in attendance file as attendees.")

    data = []
    for row in rows[header_row_idx + 1:]:
        if not row or not row[0].strip():
            continue
        name = row[name_idx].strip() if name_idx < len(row) else ""
        if not name:
            continue

        if duration_idx is not None:
            duration_str = row[duration_idx].strip() if duration_idx < len(row) else ""
            duration = parse_duration(duration_str)
            if duration is None:
                continue
            if duration < 30:
                continue  # Did not meet minimum attendance threshold

        key = parse_name_parts(name)
        if key and key not in {d["normalized_name"] for d in data}:
            data.append({"normalized_name": key})

    return data


def load_registered(path):
    rows = load_file(path)

    # Search all rows for a header containing both 'name' and 'score'
    header_row = None
    for i, row in enumerate(rows):
        headers_candidate = [h.strip() for h in row if h and h.strip()]
        has_name = any('name' in h.lower() for h in headers_candidate)
        has_score = any('score' in h.lower() for h in headers_candidate)
        if has_name and has_score:
            header_row = i
            break

    if header_row is None:
        raise KeyError("Could not find a header row with both 'Name' and 'Score' columns in registered file")

    headers = [h.strip() for h in rows[header_row]]
    find_column(headers, "name")  # Validate name column exists
    find_column(headers, "score")  # Validate score column exists
    part1_col = find_column(headers, "part1")

    name_idx = headers.index(find_column(headers, "name"))
    part1_idx = headers.index(part1_col)

    data = []
    for row in rows[header_row + 1:]:
        if len(row) > name_idx and row[name_idx].strip():
            data.append({
                "name": row[name_idx].strip(),
                "normalized_name": parse_name_parts(row[name_idx]),
                "attended": False,
            })

    return data, part1_col, part1_idx, headers, rows, header_row


def main():
    parser = argparse.ArgumentParser(
        description="Update registration scores based on Teams attendance (minimum 30 min required)."
    )
    parser.add_argument("attendance_file", help="Teams attendance report (.csv, .tsv, or .xlsx)")
    parser.add_argument("registered_file", help="Registration/roster file (.csv, .tsv, or .xlsx)")
    parser.add_argument(
        "--output",
        default="registered_scored.xlsx",
        help="Output file for updated registration (default: registered_scored.xlsx)",
    )
    args = parser.parse_args()

    if not args.output.lower().endswith(('.csv', '.xlsx')):
        args.output += '.xlsx'

    valid_attendees = load_attendance(args.attendance_file)
    registered_data, part1_col, part1_idx, headers, rows, header_row = load_registered(args.registered_file)

    for item in registered_data:
        item_backup = get_backup_key(item["normalized_name"])
        for attendee in valid_attendees:
            attendee_backup = get_backup_key(attendee["normalized_name"])
            if (item["normalized_name"] == attendee["normalized_name"] or 
                item_backup == attendee_backup or 
                item_backup[1] in attendee["normalized_name"]):
                item["attended"] = True
                break

    for item_idx, item in enumerate(registered_data):
        row_idx = header_row + 1 + item_idx
        if row_idx < len(rows):
            while len(rows[row_idx]) <= part1_idx:
                rows[row_idx].append('')
            rows[row_idx][part1_idx] = 1 if item["attended"] else 0

    if args.output.lower().endswith('.xlsx'):
        try:
            import openpyxl
        except ImportError as exc:
            raise ImportError(
                "openpyxl is required to write .xlsx files. Install it with "
                "`pip install openpyxl`."
            ) from exc
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        wb.save(args.output)
    else:
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(rows)

    attended_count = sum(1 for item in registered_data if item["attended"])
    print(f"Updated registration saved to: {args.output}")
    print(f"  {attended_count} of {len(registered_data)} registered attendees marked in Part1 (attended >= 30 min)")


if __name__ == "__main__":
    main()