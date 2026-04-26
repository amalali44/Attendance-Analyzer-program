import argparse
import re
import csv


def normalize_name(name):
    """Normalize a name to a canonical frozenset of lowercase tokens.

    This handles both "First Last" and "Last, First" formats by stripping
    punctuation and sorting tokens alphabetically, so "Cerrato, Christopher"
    and "Chris Cerrato" both reduce to the same key as long as one name is
    a prefix/alias of the other's tokens.

    Returns a frozenset of name tokens for robust set-based matching.
    """
    if not name:
        return frozenset()
    # Remove commas and collapse whitespace
    cleaned = re.sub(r"[,]+", " ", str(name))
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return frozenset(cleaned.split())


def names_match(a: frozenset, b: frozenset) -> bool:
    """Two names match if all tokens from the smaller name appear in the larger.

    This handles "Chris Cerrato" vs "Cerrato, Christopher" by checking that
    every token of the shorter name is a prefix of some token in the other.
    Exact token match is tried first; prefix match is the fallback.
    """
    if not a or not b:
        return False
    if a == b:
        return True
    # Subset match: every token in the smaller set appears in the larger
    smaller, larger = (a, b) if len(a) <= len(b) else (b, a)
    for token in smaller:
        if not any(token == t or t.startswith(token) or token.startswith(t)
                   for t in larger):
            return False
    return True


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
    for row_num, row in enumerate(rows[header_row_idx + 1:], start=header_row_idx + 2):
        if not row or not row[0].strip():
            continue
        name = row[name_idx].strip() if name_idx < len(row) else ""
        if not name:
            continue

        if duration_idx is not None:
            duration_str = row[duration_idx].strip() if duration_idx < len(row) else ""
            duration = parse_duration(duration_str)
            if duration is None:
                print(f"  Warning: could not parse duration '{duration_str}' for '{name}' (row {row_num}) — skipping")
                continue
            if duration < 30:
                continue  # Did not meet minimum attendance threshold

        key = normalize_name(name)
        if key not in {d["normalized_name"] for d in data}:
            data.append({"normalized_name": key})

    return data


def load_registered(path):
    rows = load_csv_with_encoding(path)

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
    name_col = find_column(headers, "name")
    score_col = find_column(headers, "score")
    part1_col = find_column(headers, "part1")

    name_idx = headers.index(name_col)
    score_idx = headers.index(score_col)
    part1_idx = headers.index(part1_col)

    data = []
    for row in rows[header_row + 1:]:
        if len(row) > name_idx and row[name_idx].strip():
            data.append({
                "name": row[name_idx].strip(),
                "normalized_name": normalize_name(row[name_idx]),
                "attended": False,
            })

    return data, name_col, score_col, part1_col, headers, rows, header_row, name_idx, score_idx, part1_idx


def normalize_output_path(output):
    """Ensure output path ends with .csv without corrupting filenames."""
    if not output.lower().endswith('.csv'):
        output = output + '.csv'
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Update registration scores based on Teams attendance (minimum 30 min required)."
    )
    parser.add_argument("attendance_file", help="Teams attendance report (CSV/TSV)")
    parser.add_argument("registered_file", help="Registration file (CSV/TSV)")
    parser.add_argument(
        "--output",
        default="registered_scored.csv",
        help="Output file for updated registration (default: registered_scored.csv)",
    )
    args = parser.parse_args()

    # FIX: safe extension handling — just append, never strip
    args.output = normalize_output_path(args.output)

    valid_attendees = load_attendance(args.attendance_file)
    registered_data, reg_name_col, reg_score_col, reg_part1_col, reg_headers, reg_rows, reg_header_row, name_idx, score_idx, part1_idx = load_registered(args.registered_file)

    # Match attendees by name; use names_match for fuzzy First/Last name comparison.
    for item in registered_data:
        for attendee in valid_attendees:
            if names_match(item["normalized_name"], attendee["normalized_name"]):
                item["attended"] = True
                break

    # Write Part1 column (1 = attended >= 30 min, 0 = did not)
    for item_idx, item in enumerate(registered_data):
        row_idx = reg_header_row + 1 + item_idx
        if row_idx < len(reg_rows):
            while len(reg_rows[row_idx]) <= part1_idx:
                reg_rows[row_idx].append('')
            reg_rows[row_idx][part1_idx] = 1 if item["attended"] else 0

    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(reg_rows)

    attended_count = sum(1 for item in registered_data if item["attended"])
    print(f"Updated registration saved to: {args.output}")
    print(f"  {attended_count} of {len(registered_data)} registered attendees marked in Part1 (attended >= 30 min)")


if __name__ == "__main__":
    main()