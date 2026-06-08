from flask import Flask, request, render_template_string, send_file
import os
import tempfile
from script import load_attendance, load_registered
import openpyxl

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Training Attendance Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #4CAF50, #45a049);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            font-weight: 300;
        }
        .form-group {
            margin-bottom: 25px;
            position: relative;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
            font-size: 1.1em;
        }
        .file-input-wrapper {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        .file-input-wrapper input[type="file"] {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        .file-input-label {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 15px 20px;
            border: 2px dashed #ddd;
            border-radius: 8px;
            background: #f9f9f9;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 60px;
        }
        .file-input-label:hover {
            border-color: #4CAF50;
            background: #f0f8f0;
        }
        .file-input-label span {
            color: #666;
            font-size: 1em;
        }
        .file-name {
            margin-top: 8px;
            font-size: 0.9em;
            color: #4CAF50;
            font-weight: 500;
        }
        button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
            animation: slideIn 0.5s ease-out;
        }
        .result h2 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.5em;
        }
        .result p {
            color: #666;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        .download-link {
            display: inline-block;
            background: #2196F3;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s ease;
        }
        .download-link:hover {
            background: #1976D2;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .loading.show {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #4CAF50;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 768px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Training Attendance Analyzer</h1>
        <form id="uploadForm" method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="attendance">📄 Select Attendance Report (CSV/XLSX)</label>
                <div class="file-input-wrapper">
                    <input type="file" id="attendance" name="attendance" required accept=".csv,.xlsx">
                    <div class="file-input-label">
                        <span id="attendanceText">Choose attendance file or drag & drop</span>
                    </div>
                </div>
                <div id="attendanceFileName" class="file-name"></div>
            </div>
            <div class="form-group">
                <label for="registration">📋 Select Registration File (CSV/XLSX)</label>
                <div class="file-input-wrapper">
                    <input type="file" id="registration" name="registration" required accept=".csv,.xlsx">
                    <div class="file-input-label">
                        <span id="registrationText">Choose registration file or drag & drop</span>
                    </div>
                </div>
                <div id="registrationFileName" class="file-name"></div>
            </div>
            <button type="submit" id="submitBtn">🚀 Analyze Attendance</button>
        </form>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Processing your files...</p>
        </div>
        {% if result %}
        <div class="result">
            <h2>✅ Analysis Complete</h2>
            <p>{{ result }}</p>
            <a href="/download" class="download-link">📥 Download Output File</a>
        </div>
        {% endif %}
    </div>
    <script>
        // File input handling
        function setupFileInput(inputId, textId, nameId) {
            const input = document.getElementById(inputId);
            const text = document.getElementById(textId);
            const nameDiv = document.getElementById(nameId);
            
            input.addEventListener('change', function(e) {
                if (this.files && this.files[0]) {
                    text.textContent = 'File selected: ' + this.files[0].name;
                    nameDiv.textContent = this.files[0].name;
                } else {
                    text.textContent = 'Choose file or drag & drop';
                    nameDiv.textContent = '';
                }
            });
        }
        
        setupFileInput('attendance', 'attendanceText', 'attendanceFileName');
        setupFileInput('registration', 'registrationText', 'registrationFileName');
        
        // Form submission
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const loading = document.getElementById('loading');
        
        form.addEventListener('submit', function() {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            loading.classList.add('show');
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        attendance_file = request.files.get('attendance')
        registration_file = request.files.get('registration')
        
        if not attendance_file or not registration_file:
            result = "Please select both files."
        else:
            # Save files temporarily
            temp_dir = tempfile.mkdtemp()
            attendance_path = os.path.join(temp_dir, attendance_file.filename)
            registration_path = os.path.join(temp_dir, registration_file.filename)
            attendance_file.save(attendance_path)
            registration_file.save(registration_path)
            
            try:
                # Process
                valid_attendees = load_attendance(attendance_path)
                registered_data, part1_col, part1_idx, headers, rows, header_row = load_registered(registration_path)
                
                # Match attendees to registered participants using email
                attendee_emails = {a.get("normalized_email") for a in valid_attendees if a.get("normalized_email")}
                for item in registered_data:
                    item_email = item.get("normalized_email")
                    if item_email and item_email in attendee_emails:
                        item["attended"] = True
                
                for item_idx, item in enumerate(registered_data):
                    row_idx = header_row + 1 + item_idx
                    if row_idx < len(rows):
                        while len(rows[row_idx]) <= part1_idx:
                            rows[row_idx].append('')
                        rows[row_idx][part1_idx] = 1 if item["attended"] else 0
                
                output_path = os.path.join(temp_dir, "registered_scored.xlsx")
                wb = openpyxl.Workbook()
                ws = wb.active
                for row in rows:
                    ws.append(row)
                wb.save(output_path)
                
                attended_count = sum(1 for item in registered_data if item["attended"])
                result = f"Marked {attended_count} of {len(registered_data)} attendees."
                
                # Store paths for download
                app.config['OUTPUT_FILE'] = output_path
                app.config['TEMP_DIR'] = temp_dir
                
            except Exception as e:
                result = f"Error: {str(e)}"
    
    return render_template_string(HTML_TEMPLATE, result=result)

@app.route('/download')
def download():
    if 'OUTPUT_FILE' in app.config and os.path.exists(app.config['OUTPUT_FILE']):
        return send_file(app.config['OUTPUT_FILE'], as_attachment=True, download_name="registered_scored.xlsx")
    return "File not found", 404

def main():
    """Start the Flask web server."""
    print("Starting Training Attendance Analyzer Web Server...")
    print("\nWeb Interface: http://localhost:5000")
    print("Network Access: http://<your-ip>:5000")
    print("\nPress Ctrl+C to stop the server")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    main()