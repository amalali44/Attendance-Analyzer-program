#!/usr/bin/env python3
"""
Setup script for Training Attendance Analyzer
This script helps install all required dependencies.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install requirements from requirements.txt"""
    print("\n" + "=" * 60)
    print("Training Attendance Analyzer - Setup")
    print("=" * 60)
    print("\nInstalling required packages...")
    print("This may take a few minutes...\n")
    
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("\n" + "=" * 60)
        print("✓ Installation Complete!")
        print("=" * 60)
        print("\nYou can now run the application with:")
        print("  python run.py")
        print("\n" + "=" * 60)
        return True
    except subprocess.CalledProcessError:
        print("\n" + "=" * 60)
        print("✗ Installation Failed")
        print("=" * 60)
        print("\nTry installing manually:")
        print("  pip install flask openpyxl")
        print("\n" + "=" * 60)
        return False

if __name__ == "__main__":
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found!")
        print("Please run this script from the application's root directory.")
        sys.exit(1)
    
    try:
        success = install_requirements()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
