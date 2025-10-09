#!/usr/bin/env python3
"""
Fix Central Technology customer record with correct Google Maps data
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from utils.external_data_service import ExternalDataService
from models_crm import Customer

def fix_central_technology_maps():
    """Fix Central Technology customer record with correct Google Maps data"""
    
    with app.app_context():
        # Find Central Technology customer
        customer = Customer.query.filter(
            Customer.company_name.ilike('%Central Technology%')
        ).first()
        
        if not customer:
            print("No Central Technology customer found")
            return
        
        print(f"Found customer: {customer.company_name}")
        print(f"ID: {customer.id}")
        
        # Get fresh Google Maps data
        print("\nGetting fresh Google Maps data...")
        service = ExternalDataService()
        maps_result = service.get_google_maps_data(customer.company_name, customer.website)
        
        if maps_result['success']:
            maps_data = maps_result['data']
            print(f"Found {len(maps_data.get('locations', []))} locations")
            
            # Update the customer record
            customer.google_maps_data = json.dumps(maps_data)
            
            try:
                db.session.commit()
                print(f"[OK] Successfully updated customer with {len(maps_data.get('locations', []))} Google Maps locations")
                
                # Verify the update
                db.session.refresh(customer)
                if customer.google_maps_data:
                    stored_data = json.loads(customer.google_maps_data)
                    print(f"Verification: {len(stored_data.get('locations', []))} locations stored")
                    
                    for i, location in enumerate(stored_data.get('locations', [])):
                        print(f"  {i+1}. {location.get('name', 'N/A')}")
                        print(f"     Address: {location.get('address', 'N/A')}")
                        if location.get('phone'):
                            print(f"     Phone: {location['phone']}")
                        if location.get('rating'):
                            print(f"     Rating: {location['rating']}/5")
                        print()
                
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Failed to update customer: {e}")
        else:
            print(f"[ERROR] Failed to get Google Maps data: {maps_result.get('error')}")

if __name__ == "__main__":
    fix_central_technology_maps()
