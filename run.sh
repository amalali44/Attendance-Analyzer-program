#!/bin/bash
# Training Attendance Analyzer - Mac/Linux Launcher

echo ""
echo "============================================================"
echo "Training Attendance Analyzer"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed"
    echo ""
    echo "Please install Python using:"
    echo "  • Mac: brew install python3"
    echo "  • Linux (Ubuntu/Debian): sudo apt-get install python3"
    echo "  • Linux (Fedora): sudo dnf install python3"
    echo ""
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

# Check if requirements are installed
$PYTHON -c "import flask, openpyxl" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    echo ""
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install dependencies"
        echo ""
        exit 1
    fi
fi

echo "Starting application..."
echo ""
echo "The web interface will open in your browser."
echo "If it doesn't, visit: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server."
echo "============================================================"
echo ""

# Run the application
$PYTHON run.py
