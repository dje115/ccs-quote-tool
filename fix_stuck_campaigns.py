#!/usr/bin/env python3
"""
Fix campaigns stuck in RUNNING status
"""

from app import app, db
from models_lead_generation import LeadGenerationCampaign, LeadGenerationStatus
from datetime import datetime

with app.app_context():
    # Find all campaigns stuck in RUNNING status
    stuck_campaigns = LeadGenerationCampaign.query.filter_by(
        status=LeadGenerationStatus.RUNNING
    ).all()
    
    print(f"\nFound {len(stuck_campaigns)} campaigns stuck in RUNNING status:")
    
    for campaign in stuck_campaigns:
        print(f"\n  Campaign: {campaign.name}")
        print(f"  ID: {campaign.id}")
        print(f"  Started: {campaign.started_at}")
        print(f"  Status: {campaign.status}")
        
        # Reset to DRAFT so they can be run again
        campaign.status = LeadGenerationStatus.DRAFT
        campaign.started_at = None
        campaign.completed_at = None
        
        print(f"  → Reset to DRAFT")
    
    if stuck_campaigns:
        db.session.commit()
        print(f"\n✓ Fixed {len(stuck_campaigns)} campaigns")
    else:
        print("\n✓ No stuck campaigns found")

