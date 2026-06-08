import argparse
import re
import csv
import os


def parse_name_parts(name: str):
    """Return (first_initial, last_name) from either "First Last" or "Last, First".

    Examples:
      "Nicholas Lehman"      -> ("n", "lehman")
      "Nick Lehman"          -> ("n", "lehman")
      "Lehman, Nicholas"     -> ("n", "lehman")
      "Pena Murillo, Nestor" -> ("n", "pena murillo")
    """
    if not name:
        return None, None
    cleaned = re.sub(r"\s+", " ", str(name)).strip()

    if "," in cleaned:
        # "Last, First" — everything before first comma is the last name
        parts = cleaned.split(",", 1)
        last = parts[0].strip().lower()
        first = parts[1].strip().lower()
    else:
        # "First Last..." — first token is first name, rest is last name
        tokens = cleaned.split()
        first = tokens[0].lower()
        last = " ".join(t.lower() for t in tokens[1:]) if len(tokens) > 1 else ""

    first_initial = first[0] if first else ""
    return first_initial, last


def normalize_name(name):
    """Return a (first_initial, last_name) tuple used as the match key."""
    return parse_name_parts(name)


def names_match(a, b) -> bool:
    """Match two names by first initial + last name.

    Handles nicknames (Nick/Nicholas both have initial "n") and
    both "First Last" and "Last, First" formats.
    """
    a_initial, a_last = a
    b_initial, b_last = b
    if not a_last or not b_last:
        return False
    return a_initial == b_initial and a_last == b_last


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


def load_csv_with_encoding(path):
    """Try to load CSV/TSV with different encodings and delimiters.

    For each encoding that decodes successfully, score every delimiter by the
    median number of columns it produces across non-empty rows.  Pick the
    encoding+delimiter pair with the highest score so that a tab-separated file
    is never mis-parsed as a single-column CSV just because commas are tried first.
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
                # Score = median column count across non-empty rows.
                # A UTF-16 TSV mis-parsed as UTF-8 gives single-column rows (score 1);
                # correctly decoded it gives the real column count (score 7+).
                # Evaluate ALL encoding+delimiter pairs and pick the highest scorer.
                score = statistics.median(len(row) for row in non_empty)
                if score > best_score:
                    best_score = score
                    best_rows = rows
            except Exception:
                continue

    if best_rows is not None:
        return best_rows
    raise ValueError(f"Could not decode file {path} with any supported encoding/delimiter")


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
    rows = load_csv_with_encoding(path)

    # Attendance file must have both 'Email' and 'Duration' columns
    header_row_idx = find_header_row(rows, ["email", "duration"])

    if header_row_idx is None:
        raise ValueError(
            "Attendance file: could not find a header row containing both 'Email' and 'Duration' columns.\n"
            "  Email-based comparison requires email addresses in the attendance file."
        )

    headers = [h.strip() for h in rows[header_row_idx]]

    try:
        email_col = find_column(headers, "email")
        duration_col = find_column(headers, "duration")
    except KeyError as e:
        raise KeyError(f"Attendance file header row (row {header_row_idx}): {e}")

    email_idx = headers.index(email_col)
    duration_idx = headers.index(duration_col)

    data = []
    for row in rows[header_row_idx + 1:]:
        if not row or not row[email_idx].strip():
            continue

        email = row[email_idx].strip() if email_idx < len(row) else ""
        duration_str = row[duration_idx].strip() if duration_idx < len(row) else ""
        
        if not email:
            continue

        duration = parse_duration(duration_str)
        if duration is None:
            continue
        if duration < 30:
            continue  # Did not meet minimum attendance threshold

        key = normalize_name(name)
        if key not in {d["normalized_name"] for d in data} and key != (None, None) and key[1]:
            data.append({"normalized_name": key})

    return data


def load_registered(path):
    rows = load_csv_with_encoding(path)

    # Search all rows for a header containing both 'email' and 'score'
    header_row = None
    for i, row in enumerate(rows):
        headers_candidate = [h.strip() for h in row if h and h.strip()]
        has_email = any('email' in h.lower() for h in headers_candidate)
        has_score = any('score' in h.lower() for h in headers_candidate)
        if has_email and has_score:
            header_row = i
            break

    if header_row is None:
        raise KeyError("Could not find a header row with both 'Email' and 'Score' columns in registered file")

    headers = [h.strip() for h in rows[header_row]]
    find_column(headers, "email")  # Validate email column exists
    find_column(headers, "score")  # Validate score column exists
    part1_col = find_column(headers, "part1")
    email_col = find_column(headers, "email")

    email_idx = headers.index(email_col)
    part1_idx = headers.index(part1_col)

    data = []
    for row in rows[header_row + 1:]:
        if len(row) <= email_idx or not row[email_idx].strip():
            continue
        email_value = row[email_idx].strip()
        normalized_email = normalize_email(email_value)
        if not normalized_email:
            continue
        data.append({
            "normalized_email": normalized_email,
            "attended": False,
        })

    return data, name_col, score_col, part1_col, headers, rows, header_row, name_idx, score_idx, part1_idx


def normalize_output_path(output):
    """Ensure output path ends with .csv without corrupting filenames."""
    if not output.lower().endswith(('.csv', '.xlsx')):
        output = output + '.csv'
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Update registration scores based on Teams attendance (minimum 30 min required). Comparison uses email addresses."
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

    # Create a set of normalized emails from attendees for efficient lookup
    attendee_emails = {attendee.get("normalized_email") for attendee in valid_attendees if attendee.get("normalized_email")}

    # Match registered participants to attendees using email
    for item in registered_data:
        item_email = item.get("normalized_email", "")
        if item_email and item_email in attendee_emails:
            item["attended"] = True

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