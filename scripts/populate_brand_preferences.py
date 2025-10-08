#!/usr/bin/env python3
"""
Populate database with brand preferences for different product categories.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import from app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app, db
from models import AdminSetting

# Brand preferences for different categories
brand_preferences = [
    ('cabling_brands', 'Connectix,Excel,HellermannTyton', 'Preferred cabling brands (comma-separated)'),
    ('cctv_brands', 'Unifi,Hikvision,Dahua', 'Preferred CCTV brands (comma-separated)'),
    ('wifi_brands', 'Unifi,Cisco,Meraki', 'Preferred WiFi brands (comma-separated)'),
    ('door_entry_brands', 'Paxton Net2,Unifi,2N', 'Preferred door entry brands (comma-separated)'),
    ('patch_panel_brands', 'Connectix,Excel,Panduit', 'Preferred patch panel brands (comma-separated)'),
    ('fiber_brands', 'Corning,CommScope,ADC', 'Preferred fiber optic brands (comma-separated)'),
    ('cabinet_brands', 'Connectix,Excel,Rittal', 'Preferred cabinet brands (comma-separated)'),
]

with app.app_context():
    print('Adding brand preferences...')
    
    for key, value, description in brand_preferences:
        # Check if setting already exists
        existing = AdminSetting.query.filter_by(key=key).first()
        if existing:
            print(f'Updating {key}: {value}')
            existing.value = value
        else:
            print(f'Adding {key}: {value}')
            setting = AdminSetting(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()
    print(f'Brand preferences added/updated: {len(brand_preferences)}')


