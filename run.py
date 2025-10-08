#!/usr/bin/env python3
"""
CCS Quote Tool - Startup Script
Run this script to start the application
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Set environment variables if not already set
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'ccs-quote-tool-secret-key-change-in-production'
    
    print("=" * 60)
    print("CCS Quote Tool - Starting Application")
    print("=" * 60)
    print("Access the application at: http://localhost:5000")
    print("Default login: admin / admin123")
    print("=" * 60)
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


