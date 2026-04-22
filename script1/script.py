import argparse
import re
from openpyxl import load_workbook
from openpyxl.styles import PatternFill


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


def load_attendance(path):
    wb = load_workbook(path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    
    # Skip first 8 rows and get header
    if len(rows) <= 8:
        raise ValueError("File doesn't have enough rows")
    
    headers = [h for h in rows[8] if h]
    name_col = find_column(headers, "name")
    duration_col = find_column(headers, "in meeting duration")
    
    name_idx = headers.index(name_col)
    duration_idx = headers.index(duration_col)
    
    data = []
    for row in rows[9:]:
        if row[name_idx]:  # Skip empty rows
            duration = parse_duration(row[duration_idx] if duration_idx < len(row) else None)
            short = (duration or 0) < 30
            data.append({
                "name": row[name_idx],
                "normalized_name": normalize_name(row[name_idx]),
                "duration": duration,
                "short": short
            })
    
    return data, name_col, headers


def highlight_attendance(attendance_data, name_col, input_path, output_path):
    wb = load_workbook(input_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = [h for h in rows[8] if h]
    name_idx = headers.index(name_col)
    
    red_fill = PatternFill(start_color="FFFFC7CE", end_color="FFFFC7CE", fill_type="solid")
    
    data_idx = 0
    for row_idx in range(10, ws.max_row + 1):
        if data_idx < len(attendance_data) and attendance_data[data_idx]["short"]:
            ws.cell(row=row_idx, column=name_idx + 1).fill = red_fill
        data_idx += 1
    
    wb.save(output_path)


def load_registered(path):
    wb = load_workbook(path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    
    headers = rows[0]
    name_col = find_column(headers, "name")
    score_col = find_column(headers, "score")
    
    name_idx = headers.index(name_col)
    score_idx = headers.index(score_col)
    
    data = []
    for row in rows[1:]:
        if row[name_idx]:
            data.append({
                "name": row[name_idx],
                "normalized_name": normalize_name(row[name_idx]),
                "score": row[score_idx] if score_idx < len(row) else None
            })
    
    return data, name_col, score_col, headers


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
    parser.add_argument("attendance_file", help="Excel file exported from Teams attendance")
    parser.add_argument("registered_file", help="Excel file with registered attendees")
    parser.add_argument(
        "--attendance-out",
        default="attendance_highlighted.xlsx",
        help="Output Excel file for highlighted attendance",
    )
    parser.add_argument(
        "--registered-out",
        default="registered_scored.xlsx",
        help="Output Excel file for updated registration",
    )
    args = parser.parse_args()

    attendance_data, attendance_name_col, _ = load_attendance(args.attendance_file)
    highlight_attendance(attendance_data, attendance_name_col, args.attendance_file, args.attendance_out)

    registered_data, reg_name_col, reg_score_col, reg_headers = load_registered(args.registered_file)
    registered_data = score_registered(attendance_data, registered_data, reg_name_col, reg_score_col)
    
    # Write updated registered file
    wb = load_workbook(args.registered_file)
    ws = wb.active
    
    score_col_idx = reg_headers.index(reg_score_col)
    for row_idx, item in enumerate(registered_data, start=2):
        ws.cell(row=row_idx, column=score_col_idx + 1).value = item["score"]
    
    wb.save(args.registered_out)

    print(f"Saved highlighted attendance to: {args.attendance_out}")
    print(f"Saved updated registration to: {args.registered_out}")


if __name__ == "__main__":
    main()
