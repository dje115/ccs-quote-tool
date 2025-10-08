#!/usr/bin/env python3
"""
Script to populate default admin settings
"""

import os
import sys

# Add the project root to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app, db
from models import AdminSetting

def populate_default_settings():
    """Populate default admin settings"""
    
    with app.app_context():
        print("Setting up default admin settings...")
        
        # Default settings
        default_settings = [
            ('day_rate', '600', 'Default day rate for a pair of engineers'),
            ('cost_per_mile', '0.45', 'Cost per mile for travel expenses'),
            ('company_name', 'CCS Solutions Ltd', 'Company name for quotes'),
            ('company_address', '123 Business Park, London', 'Company address for distance calculations'),
            ('company_postcode', 'SW1A 1AA', 'Company postcode for distance calculations'),
        ]
        
        # Clear existing settings
        AdminSetting.query.delete()
        db.session.commit()
        
        # Add default settings
        for key, value, description in default_settings:
            setting = AdminSetting(key=key, value=value)
            db.session.add(setting)
            print(f"Added setting: {key} = {value}")
        
        db.session.commit()
        print("Default admin settings created successfully!")

if __name__ == "__main__":
    populate_default_settings()
