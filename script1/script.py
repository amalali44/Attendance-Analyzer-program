import argparse
import re
import csv


def normalize_name(name):
    if not name:
        return ""
    return re.sub(r"\s+", " ", str(name).strip().lower())


def parse_duration(value):
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Try "MM:SS" format
    if ":" in text:
        try:
            parts = text.split(":")
            minutes = int(parts[0])
            seconds = int(parts[1]) if len(parts) > 1 else 0
            return minutes + seconds / 60
        except (ValueError, IndexError):
            pass

    # Try "X min" format
    m = re.search(r"(\d+(?:\.\d+)?)\s*min", text, re.I)
    if m:
        return float(m.group(1))

    # Try just a number
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1))

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
    """Try to load CSV/TSV with different encodings and delimiters"""
    encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    delimiters = [',', '\t']
    
    for encoding in encodings:
        try:
            with open(path, 'r', newline='', encoding=encoding) as f:
                content = f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        
        for delimiter in delimiters:
            try:
                rows = list(csv.reader(content.splitlines(), delimiter=delimiter))
                if rows and any(len(row) > 1 for row in rows):
                    return rows
            except:
                continue
    
    raise ValueError(f"Could not decode file {path} with any supported encoding/delimiter")


def load_attendance(path):
    rows = load_csv_with_encoding(path)
    
    if len(rows) <= 9:
        raise ValueError("Attendance file doesn't have enough rows")
    
    data = []
    for row in rows[9:]:
        if row and row[0].strip():
            name = row[0].strip()
            duration_str = row[3].strip() if len(row) > 3 else None
            duration = parse_duration(duration_str)
            if (duration or 0) >= 30:
                data.append({"normalized_name": normalize_name(name)})
    
    return data


def load_registered(path):
    rows = load_csv_with_encoding(path)
    
    header_row = None
    for candidate in [6, 0]:
        if candidate < len(rows):
            headers = [h.strip() for h in rows[candidate] if h and h.strip()]
            if any('name' in h.lower() for h in headers) and any('score' in h.lower() for h in headers):
                header_row = candidate
                break
    
    if header_row is None:
        raise KeyError("Could not find header row with 'Name' and 'Score' columns in registered file")
    
    headers = [h.strip() for h in rows[header_row]]
    name_col = find_column(headers, "name")
    score_col = find_column(headers, "score")
    
    name_idx = headers.index(name_col)
    score_idx = headers.index(score_col)
    
    data = []
    for row in rows[header_row + 1:]:
        if len(row) > name_idx and row[name_idx].strip():
            data.append({
                "name": row[name_idx].strip(),
                "normalized_name": normalize_name(row[name_idx]),
                "score": row[score_idx].strip() if score_idx < len(row) else None
            })
    
    return data, name_col, score_col, headers, rows, header_row, name_idx, score_idx


def main():
    parser = argparse.ArgumentParser(
        description="Update registration scores based on Teams attendance (minimum 30 min required)."
    )
    parser.add_argument("attendance_file", help="Teams attendance report (CSV/TSV)")
    parser.add_argument("registered_file", help="Registration file (CSV/TSV)")
    parser.add_argument(
        "--output",
        default="registered_scored.csv",
        help="Output file for updated registration (will append .csv if missing)",
    )
    args = parser.parse_args()

    if not args.output.lower().endswith('.csv'):
        args.output = args.output.rstrip('.') + '.csv'

    valid_attendees = load_attendance(args.attendance_file)
    registered_data, reg_name_col, reg_score_col, reg_headers, reg_rows, reg_header_row, name_idx, score_idx = load_registered(args.registered_file)
    
    valid_names = {item["normalized_name"] for item in valid_attendees}
    for item in registered_data:
        if item["normalized_name"] in valid_names:
            item["score"] = 1
    
    for item_idx, item in enumerate(registered_data):
        row_idx = reg_header_row + 1 + item_idx
        if row_idx < len(reg_rows):
            while len(reg_rows[row_idx]) <= score_idx:
                reg_rows[row_idx].append('')
            reg_rows[row_idx][score_idx] = item["score"]
    
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(reg_rows)
    
    print(f"Updated registration saved to: {args.output}")


if __name__ == "__main__":
    main()
