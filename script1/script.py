import argparse
import re
import csv
import os


def normalize_email(value: str):
    """Normalize email address for case-insensitive matching."""
    if not value:
        return ""
    return str(value).strip().lower()


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
    try:
        import openpyxl  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "openpyxl is required to read .xlsx files. Install it with `pip install openpyxl`."
        ) from exc
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append([("" if cell is None else str(cell).strip()) for cell in row])
    return rows


def load_csv_with_encoding(path):
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
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xlsx', '.xlsm'):
        return load_xlsx(path)
    return load_csv_with_encoding(path)


def find_header_row(rows, required_keywords):
    for i, row in enumerate(rows):
        cells_lower = [c.strip().lower() for c in row if c and c.strip()]
        if all(any(kw in cell for cell in cells_lower) for kw in required_keywords):
            return i
    return None


def parse_duration(value):
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None

    h = m_val = s = 0
    mh = re.search(r"(\d+)\s*h", text, re.I)
    mm = re.search(r"(\d+)\s*m(?!in|s)", text, re.I)
    ms = re.search(r"(\d+)\s*s(?!\w)", text, re.I)
    if mh or mm or ms:
        if mh:
            h = int(mh.group(1))
        if mm:
            m_val = int(mm.group(1))
        if ms:
            s = int(ms.group(1))
        return h * 60 + m_val + s / 60

    m_min = re.search(r"(\d+(?:\.\d+)?)\s*min", text, re.I)
    if m_min:
        return float(m_min.group(1))

    if re.search(r"^\d{1,3}:\d{2}$", text.strip()):
        try:
            parts = text.split(":")
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes + seconds / 60
        except (ValueError, IndexError):
            pass

    m_num = re.search(r"^(\d+(?:\.\d+)?)$", text.strip())
    if m_num:
        return float(m_num.group(1))

    return None


def load_attendance(path):
    rows = load_file(path)

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
        if not row or len(row) <= email_idx or not row[email_idx].strip():
            continue
        email = row[email_idx].strip() if email_idx < len(row) else ""
        duration_str = row[duration_idx].strip() if duration_idx < len(row) else ""
        if not email:
            continue
        duration = parse_duration(duration_str)
        if duration is None:
            continue
        if duration < 30:
            continue
        normalized_email = normalize_email(email)
        if not normalized_email:
            continue
        if normalized_email not in {d.get("normalized_email") for d in data}:
            data.append({"attended": True, "normalized_email": normalized_email})
    return data


def load_registered(path):
    rows = load_file(path)

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
    find_column(headers, "email")
    find_column(headers, "score")
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
        data.append({"normalized_email": normalized_email, "attended": False})

    return data, part1_col, part1_idx, headers, rows, header_row


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

    attendee_emails = {attendee.get("normalized_email") for attendee in valid_attendees if attendee.get("normalized_email")}

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
