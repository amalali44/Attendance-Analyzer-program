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
    lower_map = {h.lower(): h for h in headers if h}
    if expected.lower() not in lower_map:
        raise KeyError(f"Missing required column '{expected}'. Available: {headers}")
    return lower_map[expected.lower()]


def load_csv_with_encoding(path):
    """Try to load CSV/TSV with different encodings and delimiters"""
    encodings = ['utf-16', 'utf-8', 'latin-1', 'cp1252']
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
                if rows:
                    return rows
            except:
                continue
    
    raise ValueError(f"Could not decode file {path} with any supported encoding/delimiter")


def load_attendance(path):
    rows = load_csv_with_encoding(path)
    
    # Skip first 8 rows and get header
    if len(rows) <= 10:
        raise ValueError("File doesn't have enough rows")
    
    headers = [h.strip() for h in rows[8] if h and h.strip()]
    name_col = find_column(headers, "2. Participants")
    duration_col = find_column(headers, "in meeting duration")
    
    name_idx = headers.index(name_col)
    duration_idx = headers.index(duration_col)
    
    data = []
    for row in rows[10:]:
        if len(row) > name_idx and row[name_idx].strip():  # Skip empty rows
            duration = parse_duration(row[duration_idx].strip() if duration_idx < len(row) else None)
            short = (duration or 0) < 30
            data.append({
                "name": row[name_idx].strip(),
                "normalized_name": normalize_name(row[name_idx]),
                "duration": duration,
                "short": short
            })
    
    return data, name_col, headers, rows


def highlight_attendance(attendance_data, name_col, input_path, output_path, all_rows):
    # For CSV, add a FLAG column to mark short attendance
    headers = [h.strip() for h in all_rows[8] if h and h.strip()]
    name_idx = headers.index(name_col)
    
    # Add a FLAG column header if not present
    if "FLAG" not in headers:
        all_rows[8].append("FLAG")
    
    # Mark short attendance rows
    data_idx = 0
    for row_idx in range(9, min(9 + len(attendance_data), len(all_rows))):
        # Ensure row has enough columns
        while len(all_rows[row_idx]) <= len(headers):
            all_rows[row_idx].append('')
        
        if data_idx < len(attendance_data) and attendance_data[data_idx]["short"]:
            all_rows[row_idx][len(headers)] = "SHORT"
        data_idx += 1
    
    # Write to output
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)


def load_registered(path):
    rows = load_csv_with_encoding(path)
    
    headers = [h.strip() for h in rows[0] if h and h.strip()]
    name_col = find_column(headers, "name")
    score_col = find_column(headers, "score")
    
    name_idx = headers.index(name_col)
    score_idx = headers.index(score_col)
    
    data = []
    for row in rows[1:]:
        if len(row) > name_idx and row[name_idx].strip():
            data.append({
                "name": row[name_idx].strip(),
                "normalized_name": normalize_name(row[name_idx]),
                "score": row[score_idx].strip() if score_idx < len(row) else None
            })
    
    return data, name_col, score_col, headers, rows


def score_registered(attendance_data, registered_data, registered_name_col, score_col):
    valid_names = {item["normalized_name"] for item in attendance_data if not item["short"]}
    
    for item in registered_data:
        if item["normalized_name"] in valid_names:
            item["score"] = 1
    
    return registered_data


def main():
    parser = argparse.ArgumentParser(
        description="Parse Teams attendance, highlight short attendees, and update registration scores."
    )
    parser.add_argument("attendance_file", help="CSV/TSV file exported from Teams attendance")
    parser.add_argument("registered_file", help="CSV/TSV file with registered attendees")
    parser.add_argument(
        "--attendance-out",
        default="attendance_highlighted.csv",
        help="Output CSV file for highlighted attendance",
    )
    parser.add_argument(
        "--registered-out",
        default="registered_scored.csv",
        help="Output CSV file for updated registration",
    )
    args = parser.parse_args()

    attendance_data, attendance_name_col, _, all_rows = load_attendance(args.attendance_file)
    highlight_attendance(attendance_data, attendance_name_col, args.attendance_file, args.attendance_out, all_rows)

    registered_data, reg_name_col, reg_score_col, reg_headers, reg_rows = load_registered(args.registered_file)
    registered_data = score_registered(attendance_data, registered_data, reg_name_col, reg_score_col)
    
    # Write updated registered file
    score_col_idx = reg_headers.index(reg_score_col)
    for item_idx, item in enumerate(registered_data):
        if item_idx + 1 < len(reg_rows):
            # Ensure row has enough columns
            while len(reg_rows[item_idx + 1]) <= score_col_idx:
                reg_rows[item_idx + 1].append('')
            reg_rows[item_idx + 1][score_col_idx] = item["score"]
    
    with open(args.registered_out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(reg_rows)

    print(f"Saved highlighted attendance to: {args.attendance_out}")
    print(f"Saved updated registration to: {args.registered_out}")


if __name__ == "__main__":
    main()
