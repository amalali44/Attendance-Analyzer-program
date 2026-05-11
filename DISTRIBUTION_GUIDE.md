# Distribution Guide - Training Attendance Analyzer

This guide explains how to distribute and run the Training Attendance Analyzer on other machines.

## Quick Start for End Users

### Option 1: Python Script (Recommended for users with Python installed)

1. **Install Python** (if not already installed)
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Install Dependencies**
   - Open Command Prompt (Windows) or Terminal (Mac/Linux)
   - Navigate to the application folder
   - Run:
     ```bash
     pip install -r requirements.txt
     ```

3. **Run the Application**
   - Double-click `run.py` on Windows
   - Or from Command Prompt/Terminal:
     ```bash
     python run.py
     ```
   - The web interface will open automatically in your browser

### Option 2: Standalone Executable (Windows/Mac/Linux)

For users who don't have Python installed, you can create a standalone executable:

**Creating the Executable:**

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller attendance_analyzer.spec
   ```

3. The executable will be in the `dist/` folder

**Running the Executable:**
- Double-click `TrainingAttendanceAnalyzer.exe` (Windows)
- Or run from terminal:
  ```bash
  ./dist/TrainingAttendanceAnalyzer
  ```

## File Structure

```
training-attendance-python-script/
├── run.py                          # Main launcher script
├── requirements.txt                # Python dependencies
├── attendance_analyzer.spec        # PyInstaller configuration
├── script1/
│   ├── script.py                   # Core processing logic
│   ├── web_gui.py                  # Web interface
│   └── gui.py                      # Alternative GUI/CLI interface
└── README.md                        # Documentation
```

## For Distributing to Others

### Option 1: Source Code Distribution
Send these files to users:
- `run.py`
- `requirements.txt`
- `script1/` folder (all Python files)
- `DISTRIBUTION_GUIDE.md` (this file)

Users will need to:
1. Install Python
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python run.py`

### Option 2: Standalone Executable Distribution
After building with PyInstaller:
1. Zip the contents of `dist/TrainingAttendanceAnalyzer/` folder
2. Send to users
3. Users can extract and run the executable directly (no Python required)

### Option 3: Create an Installer
For a more professional distribution:

**Using NSIS (Windows):**
```bash
pip install cx_Freeze
```

Then create an installer wrapper around the executable.

**Using Homebrew (Mac):**
Create a tap or formula for easy installation.

## System Requirements

### For Python Script Version:
- **OS**: Windows, macOS, or Linux
- **Python**: 3.6 or higher
- **RAM**: 512 MB minimum
- **Disk Space**: ~50 MB (with dependencies)
- **Network**: Required (for web interface access)

### For Standalone Executable:
- **OS**: Windows, macOS, or Linux (choose the correct build)
- **RAM**: 512 MB minimum
- **Disk Space**: ~100 MB minimum
- **Network**: Required (for web interface access)

## Troubleshooting

### "Python not found" or "python is not recognized"
- Make sure Python is installed and added to PATH
- Try: `python3 run.py` instead of `python run.py`

### "Module not found" error
- Make sure you installed requirements:
  ```bash
  pip install -r requirements.txt
  ```

### Browser doesn't open automatically
- The server will still be running
- Manually open: http://localhost:5000

### Port 5000 already in use
- Edit `run.py` and change the port number in the last line:
  ```python
  app.run(debug=False, host='0.0.0.0', port=5001)  # Change 5000 to another port
  ```

### On Mac/Linux: Permission Denied
- Make the script executable:
  ```bash
  chmod +x run.py
  ```
- Then run: `./run.py`

## Network Access

The application runs on `0.0.0.0:5000` which means:
- **Local access**: `http://localhost:5000`
- **Network access**: `http://<your-ip>:5000` (from other computers on same network)
- **Remote access**: Use port forwarding or VPN if accessing from internet

To find your IP address:
- **Windows**: `ipconfig` in Command Prompt
- **Mac/Linux**: `ifconfig` in Terminal

## Advanced Configuration

### Change Port
Edit `run.py` and modify the port in the `app.run()` call:
```python
app.run(debug=False, host='0.0.0.0', port=8080)
```

### Enable Debug Mode
Edit `run.py` and change:
```python
app.run(debug=False, ...)  # Change to debug=True
```

### Allow Remote Connections from Any IP
The app already allows this with `0.0.0.0`. To restrict to localhost only:
```python
app.run(debug=False, host='127.0.0.1', port=5000)
```

## Support & Documentation

For detailed information about the script's functionality, see `README.md`.

For technical issues:
1. Check the error message
2. Review the troubleshooting section above
3. Verify all files are in the correct location
4. Ensure Python version is 3.6 or higher: `python --version`

## Creating Portable USB Drive

To distribute via USB:
1. Build the standalone executable (Option 2)
2. Copy the `dist/TrainingAttendanceAnalyzer/` folder to USB
3. Users can run the executable directly from USB on any compatible computer
4. No installation required!

## Version Information

- **Application**: Training Attendance Analyzer v1.0
- **Python**: 3.6+
- **Flask**: 3.1.3
- **openpyxl**: 3.1.5
