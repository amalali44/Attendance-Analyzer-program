#!/usr/bin/env python3
"""
Training Attendance Analyzer - Launcher
This script starts the Training Attendance Analyzer web application.
"""

import os
import sys
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    required = ['flask', 'openpyxl']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("=" * 60)
        print("Missing Dependencies")
        print("=" * 60)
        print(f"\nThe following packages are required but not installed:")
        for pkg in missing:
            print(f"  • {pkg}")
        print(f"\nPlease install them using:")
        print(f"\n  pip install -r requirements.txt")
        print("\nOr manually:")
        print(f"\n  pip install {' '.join(missing)}")
        print("\n" + "=" * 60)
        return False
    return True

def main():
    """Main launcher function."""
    print("\n" + "=" * 60)
    print("Training Attendance Analyzer")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Change to script directory
    script_dir = Path(__file__).parent / "script1"
    os.chdir(script_dir)
    
    # Add parent directory to path so we can import script
    sys.path.insert(0, str(script_dir))
    
    print("\nStarting application...")
    print("\nThe web interface will open in your browser.")
    print("If it doesn't open automatically, visit:")
    print("\n  → http://localhost:5000")
    print("\nPress Ctrl+C to stop the server.")
    print("=" * 60 + "\n")
    
    # Import and run the web GUI
    from web_gui import app
    
    # Open browser after a short delay
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5000')
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Please open http://localhost:5000 manually in your browser")
    
    # Run the Flask app
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
