# Quick Start Guide - Training Attendance Analyzer

## 🚀 Get Started in 3 Steps

### Step 1: Check Python Installation
```bash
python --version
```
Should show Python 3.6 or higher. If not installed, download from https://www.python.org/downloads/

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

**Windows:**
- Double-click `run.bat`
- Or: `python run.py`

**Mac/Linux:**
- Make executable: `chmod +x run.sh`
- Run: `./run.sh`
- Or: `python3 run.py`

The web interface will open automatically on `http://localhost:5000`

---

## 📝 Using the Application

### Upload Files
1. Select your **Attendance Report** (Teams export or roster CSV/XLSX)
2. Select your **Registration File** (LMS export CSV/XLSX)

### Do the Analysis
- Click **"Analyze Attendance"**
- Wait for processing to complete

### Download Results
- Click **"Download Output File"**
- The updated registration file with attendance marked in the `Part1` column

---

## 📦 For Distributing to Others

### Option 1: Send Source Code
1. Zip these files:
   - `script1/` folder
   - `run.py`
   - `run.bat` (for Windows users)
   - `run.sh` (for Mac/Linux users)
   - `requirements.txt`
   - `QUICKSTART.md` (this file)

2. Recipients:
   - Install Python
   - Run: `pip install -r requirements.txt`
   - Run: `python run.py` or double-click `run.bat`

### Option 2: Create Standalone Executable (No Python Required)
```bash
pip install pyinstaller
pyinstaller attendance_analyzer.spec
```

Then zip the `dist/TrainingAttendanceAnalyzer/` folder and send to others.

See `DISTRIBUTION_GUIDE.md` for detailed instructions.

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python from https://www.python.org/downloads/ |
| "Module not found" | Run: `pip install -r requirements.txt` |
| Browser doesn't open | Visit `http://localhost:5000` manually |
| Port 5000 in use | Edit `run.py` and change port number |
| Mac/Linux: "Permission denied" | Run: `chmod +x run.sh` |

---

## 🌐 Network Access

The application runs on `0.0.0.0:5000`:
- **Local**: `http://localhost:5000`
- **Network**: `http://<your-ip>:5000`

Find your IP:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig`

---

## 📖 For More Information

- See `README.md` for detailed technical documentation
- See `DISTRIBUTION_GUIDE.md` for distribution options
- See `script1/script.py` for algorithm details
