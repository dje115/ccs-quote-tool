#!/usr/bin/env python3
"""
Standalone campaign worker - runs independently of Flask
Usage: python campaign_worker.py <campaign_id>
"""
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models_lead_generation import LeadGenerationCampaign, LeadGenerationStatus
from utils.lead_generation_service import LeadGenerationService
from datetime import datetime

def run_campaign_standalone(campaign_id):
    """Run campaign in standalone process"""
    with app.app_context():
        try:
            campaign = LeadGenerationCampaign.query.get(campaign_id)
            if not campaign:
                print(f"[ERROR] Campaign {campaign_id} not found")
                return
            
            print(f"[STANDALONE] Starting campaign {campaign_id}...")
            print(f"[STANDALONE] Campaign: {campaign.name}")
            print(f"[STANDALONE] Type: {campaign.prompt_type}")
            
            # Initialize service
            service = LeadGenerationService()
            
            # Generate leads
            result = service.generate_leads(campaign)
            
            if result['success']:
                # Create lead records
                leads_result = service.create_leads_from_campaign(campaign, result['leads'])
                db.session.commit()
                
                print(f"[STANDALONE] SUCCESS! Campaign {campaign_id} completed")
                print(f"[STANDALONE] Found {result['total_found']} leads")
                print(f"[STANDALONE] Created {leads_result['leads_created']} new leads")
            else:
                print(f"[STANDALONE] FAILED: {result['error']}")
                campaign.status = LeadGenerationStatus.FAILED
                campaign.completed_at = datetime.utcnow()
                db.session.commit()
                
        except Exception as e:
            print(f"[STANDALONE] CRASHED: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                campaign = LeadGenerationCampaign.query.get(campaign_id)
                if campaign:
                    campaign.status = LeadGenerationStatus.FAILED
                    campaign.completed_at = datetime.utcnow()
                    db.session.commit()
            except:
                pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python campaign_worker.py <campaign_id>")
        sys.exit(1)
    
    campaign_id = int(sys.argv[1])
    run_campaign_standalone(campaign_id)

