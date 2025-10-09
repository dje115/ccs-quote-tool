#!/usr/bin/env python3
"""
Manually update Central Technology with all 4 Google Maps locations
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models_crm import Customer

def update_with_all_locations():
    """Manually update Central Technology with all 4 locations"""
    
    with app.app_context():
        # Find Central Technology customer
        customer = Customer.query.filter(
            Customer.company_name.ilike('%Central Technology%')
        ).first()
        
        if not customer:
            print("No Central Technology customer found")
            return
        
        print(f"Found customer: {customer.company_name}")
        
        # Create the correct Google Maps data with all 4 locations
        # Based on our previous tests, we know these are the locations
        maps_data = {
            'locations': [
                {
                    'name': 'Central Technology Ltd',
                    'address': 'Quantum Point, Sheepbridge Works, Sheepbridge Ln, Chesterfield S41 9RX, UK',
                    'phone': '+44 1246 266130',
                    'rating': 4.6,
                    'type': 'establishment'
                },
                {
                    'name': 'Central Technology Dorset',
                    'address': '17 Cobham Rd, Ferndown, Wimborne BH21 7PE, UK',
                    'phone': '',
                    'rating': 0,
                    'type': 'establishment'
                },
                {
                    'name': 'Central Technology Leicester',
                    'address': 'Office1, The Barn, Bridge Farm, Holt Ln, Leicester LE17 5NJ, UK',
                    'phone': '',
                    'rating': 0,
                    'type': 'establishment'
                },
                {
                    'name': 'Central Retail Digital',
                    'address': 'Quantum Point, Sheepbridge Works, Sheepbridge Ln, Chesterfield S41 9RX, UK',
                    'phone': '',
                    'rating': 0,
                    'type': 'establishment'
                }
            ],
            'addresses': [
                'Quantum Point, Sheepbridge Works, Sheepbridge Ln, Chesterfield S41 9RX, UK',
                '17 Cobham Rd, Ferndown, Wimborne BH21 7PE, UK',
                'Office1, The Barn, Bridge Farm, Holt Ln, Leicester LE17 5NJ, UK'
            ],
            'phone_numbers': ['+44 1246 266130'],
            'business_hours': [],
            'ratings': [4.6],
            'place_id': None,
            'additional_locations': []
        }
        
        # Update the customer record
        customer.google_maps_data = json.dumps(maps_data)
        
        try:
            db.session.commit()
            print(f"[OK] Successfully updated customer with {len(maps_data['locations'])} Google Maps locations")
            
            # Verify the update
            db.session.refresh(customer)
            if customer.google_maps_data:
                stored_data = json.loads(customer.google_maps_data)
                print(f"Verification: {len(stored_data.get('locations', []))} locations stored")
                
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to update customer: {e}")

if __name__ == "__main__":
    update_with_all_locations()
