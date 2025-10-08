#!/usr/bin/env python3
"""
Reliable startup script for CCS Quote Tool
"""

import os
import sys
import subprocess

def start_app():
    """Start the CCS Quote Tool application"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Script directory: {script_dir}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Change to the script directory
    os.chdir(script_dir)
    
    print(f"Changed to directory: {os.getcwd()}")
    
    # Check if app.py exists
    app_file = os.path.join(script_dir, "app.py")
    if not os.path.exists(app_file):
        print(f"ERROR: app.py not found at {app_file}")
        print("Files in current directory:")
        for item in os.listdir("."):
            print(f"  {item}")
        return False
    
    print(f"Found app.py at: {app_file}")
    
    # Start the application
    try:
        print("Starting Flask application...")
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_app()


