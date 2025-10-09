#!/usr/bin/env python3
"""
Lead generation routes for AI-powered lead finding
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db
from datetime import datetime, timedelta
import json
import subprocess
import sys
import os
from models_lead_generation import (
    LeadGenerationCampaign, Lead, LeadGenerationStatus, LeadStatus, 
    LeadSource, LeadGenerationPrompt
)
from models_crm import Customer, CustomerStatus, ContactRole, BusinessSector
from utils.lead_generation_service import LeadGenerationService
from sqlalchemy import or_, and_, desc
import re

lead_generation_bp = Blueprint('lead_generation', __name__)

def map_business_sector_to_enum(sector_value):
    """Map AI-generated business sector values to enum values"""
    if not sector_value:
        return None
    
    # Convert to lowercase for comparison
    sector_lower = sector_value.lower()
    
    # Mapping dictionary for common AI-generated values
    sector_mapping = {
        'managed it / msp': BusinessSector.TECHNOLOGY,
        'managed it services': BusinessSector.TECHNOLOGY,
        'msp': BusinessSector.TECHNOLOGY,
        'it support': BusinessSector.TECHNOLOGY,
        'it services': BusinessSector.TECHNOLOGY,
        'software development': BusinessSector.TECHNOLOGY,
        'technology': BusinessSector.TECHNOLOGY,
        'tech': BusinessSector.TECHNOLOGY,
        'telecoms': BusinessSector.TECHNOLOGY,
        'telecommunications': BusinessSector.TECHNOLOGY,
        'network cabling': BusinessSector.TECHNOLOGY,
        'office': BusinessSector.OFFICE,
        'retail': BusinessSector.RETAIL,
        'industrial': BusinessSector.INDUSTRIAL,
        'healthcare': BusinessSector.HEALTHCARE,
        'health': BusinessSector.HEALTHCARE,
        'education': BusinessSector.EDUCATION,
        'school': BusinessSector.EDUCATION,
        'university': BusinessSector.EDUCATION,
        'hospitality': BusinessSector.HOSPITALITY,
        'hotel': BusinessSector.HOSPITALITY,
        'manufacturing': BusinessSector.MANUFACTURING,
        'finance': BusinessSector.FINANCE,
        'financial': BusinessSector.FINANCE,
        'government': BusinessSector.GOVERNMENT,
        'public sector': BusinessSector.GOVERNMENT,
    }
    
    # Check if the sector matches any mapping
    for key, enum_value in sector_mapping.items():
        if key in sector_lower:
            return enum_value
    
    # If no mapping found, try direct enum match
    try:
        return BusinessSector(sector_lower)
    except ValueError:
        # Default to TECHNOLOGY for IT-related businesses, OTHER for everything else
        if any(tech_term in sector_lower for tech_term in ['it', 'tech', 'software', 'computer', 'digital', 'cyber']):
            return BusinessSector.TECHNOLOGY
        return BusinessSector.OTHER

def extract_postcode(address):
    """Extract UK postcode from address string"""
    if not address:
        return None
    
    # UK postcode pattern (basic)
    postcode_pattern = r'[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}'
    match = re.search(postcode_pattern, address.upper())
    
    if match:
        return match.group(0)
    
    return None

# Background worker function for long-running campaigns
def run_campaign_worker(app, campaign_id):
    """Background worker to run campaign without blocking Flask"""
    with app.app_context():
        try:
            campaign = LeadGenerationCampaign.query.get(campaign_id)
            if not campaign:
                print(f"[ERROR] Campaign {campaign_id} not found")
                return
            
            print(f"[WORKER] Starting campaign {campaign_id} in background thread...")
            
            # Initialize lead generation service
            service = LeadGenerationService()
            
            # Generate leads
            result = service.generate_leads(campaign)
            
            if result['success']:
                # Create lead records
                leads_result = service.create_leads_from_campaign(campaign, result['leads'])
                db.session.commit()
                
                print(f"[WORKER] Campaign {campaign_id} completed successfully!")
                print(f"[WORKER] Found {result['total_found']} leads, created {leads_result['leads_created']} new leads")
            else:
                print(f"[WORKER] Campaign {campaign_id} failed: {result['error']}")
                campaign.status = LeadGenerationStatus.FAILED
                campaign.completed_at = datetime.utcnow()
                db.session.commit()
                
        except Exception as e:
            print(f"[WORKER] Campaign {campaign_id} crashed: {str(e)}")
            import traceback
            print(f"[WORKER] Traceback: {traceback.format_exc()}")
            
            try:
                campaign = LeadGenerationCampaign.query.get(campaign_id)
                if campaign:
                    campaign.status = LeadGenerationStatus.FAILED
                    campaign.completed_at = datetime.utcnow()
                    db.session.commit()
            except:
                pass

# Pre-defined prompts
DEFAULT_PROMPTS = [
    {
        'name': 'IT/MSP Expansion',
        'prompt_type': 'it_msp_expansion',
        'description': 'Find IT/MSP businesses that would benefit from adding structured cabling to their portfolio',
        'requires_company_name': False
    },
    {
        'name': 'IT/MSP Service Gaps',
        'prompt_type': 'it_msp_gaps',
        'description': 'Find IT/MSP businesses that don\'t currently offer cabling services',
        'requires_company_name': False
    },
    {
        'name': 'Similar Business Lookup',
        'prompt_type': 'similar_business',
        'description': 'Find businesses similar to a specific company',
        'requires_company_name': True
    },
    {
        'name': 'Competitor Verification',
        'prompt_type': 'competitor_verification',
        'description': 'Verify and collect data for identified competitor companies',
        'requires_company_name': False
    },
    {
        'name': 'Education Sector',
        'prompt_type': 'education',
        'description': 'Find schools and educational institutions likely to need cabling work',
        'requires_company_name': False
    },
    {
        'name': 'Healthcare Facilities',
        'prompt_type': 'healthcare',
        'description': 'Find healthcare facilities that may need network upgrades',
        'requires_company_name': False
    },
    {
        'name': 'New Businesses',
        'prompt_type': 'new_businesses',
        'description': 'Find new businesses that have opened recently and need IT infrastructure',
        'requires_company_name': False
    },
    {
        'name': 'Planning Applications',
        'prompt_type': 'planning_applications',
        'description': 'Find businesses with recent planning applications for construction/renovation',
        'requires_company_name': False
    },
    {
        'name': 'Manufacturing',
        'prompt_type': 'manufacturing',
        'description': 'Find manufacturing companies modernizing their operations',
        'requires_company_name': False
    },
    {
        'name': 'Retail & Office',
        'prompt_type': 'retail_office',
        'description': 'Find retail and office businesses renovating or expanding',
        'requires_company_name': False
    }
]

@lead_generation_bp.route('/')
@login_required
def dashboard():
    """Lead generation dashboard"""
    # Get recent campaigns
    recent_campaigns = LeadGenerationCampaign.query.filter_by(created_by=current_user.id)\
        .order_by(desc(LeadGenerationCampaign.created_at)).limit(10).all()
    
    # Get lead statistics
    total_leads = Lead.query.join(LeadGenerationCampaign)\
        .filter(LeadGenerationCampaign.created_by == current_user.id).count()
    
    new_leads = Lead.query.join(LeadGenerationCampaign)\
        .filter(LeadGenerationCampaign.created_by == current_user.id,
                Lead.status == LeadStatus.NEW).count()
    
    converted_leads = Lead.query.join(LeadGenerationCampaign)\
        .filter(LeadGenerationCampaign.created_by == current_user.id,
                Lead.status == LeadStatus.CONVERTED).count()
    
    # Get recent leads
    recent_leads = Lead.query.join(LeadGenerationCampaign)\
        .filter(LeadGenerationCampaign.created_by == current_user.id)\
        .order_by(desc(Lead.created_at)).limit(10).all()
    
    return render_template('lead_generation/dashboard.html',
                         recent_campaigns=recent_campaigns,
                         recent_leads=recent_leads,
                         stats={
                             'total_leads': total_leads,
                             'new_leads': new_leads,
                             'converted_leads': converted_leads
                         })

@lead_generation_bp.route('/create-addresses-campaign', methods=['POST'])
@login_required
def create_addresses_campaign():
    """Create a lead generation campaign based on verified addresses"""
    try:
        data = request.get_json()
        addresses = data.get('addresses', [])
        source_company = data.get('source_company', 'Unknown Company')
        
        if not addresses:
            return jsonify({
                'success': False,
                'error': 'No addresses provided'
            }), 400
        
        # Generate campaign name
        now = datetime.utcnow()
        date_time = now.strftime('%d-%m-%Y %H-%M')
        campaign_name = f"Locations of {source_company} - {date_time}"
        
        # Create campaign
        campaign = LeadGenerationCampaign(
            name=campaign_name,
            description=f"Location-based lead generation campaign targeting businesses in the same areas as {source_company}. Automatically generated from verified addresses.",
            prompt_type='location_based',
            postcode="LE1 1AA",  # Default Leicester postcode
            distance_miles=50,   # Reasonable search radius
            max_results=len(addresses) * 10,  # Allow for multiple leads per location
            created_by=current_user.id,
            status=LeadGenerationStatus.DRAFT,
            search_criteria_used={"target_locations": [addr['name'] for addr in addresses]}
        )
        
        db.session.add(campaign)
        db.session.flush()  # Get campaign ID
        
        # Create initial leads for each selected address
        for address in addresses:
            # Check for duplicates
            existing_lead = Lead.query.filter_by(
                company_name=address['name'],
                created_by=current_user.id
            ).first()
            
            if existing_lead:
                print(f"[ADDRESS CAMPAIGN] Skipping duplicate: {address['name']}")
                continue
            
            # Extract postcode from address for targeted search
            postcode = extract_postcode(address.get('address', ''))
            
            lead = Lead(
                campaign_id=campaign.id,
                company_name=address['name'],
                website=None,  # Don't put address in website field - it's not a URL
                address=address.get('address', ''),
                postcode=postcode,
                business_sector='technology',  # Default as string
                company_size="Medium",  # Default
                contact_name='',
                contact_email='',
                contact_phone=address.get('phone', ''),
                status=LeadStatus.NEW,
                lead_score=50,  # Default score
                potential_project_value=0,
                timeline_estimate="Unknown",
                created_by=current_user.id,
                notes=f"Selected address from {source_company} - {address.get('type', 'unknown')} type"
            )
            db.session.add(lead)
            print(f"[ADDRESS CAMPAIGN] Created lead for selected address: {address['name']}")
        
        # Set campaign status to running and start background process
        campaign.status = LeadGenerationStatus.RUNNING
        campaign.started_at = now
        db.session.commit()
        
        # Start background campaign
        def run_address_campaign():
            from app import app
            with app.app_context():
                try:
                    from utils.lead_generation_service import LeadGenerationService
                    service = LeadGenerationService()
                    
                    # Use location-based search for each address
                    for address in addresses:
                        print(f"[ADDRESS CAMPAIGN] Processing location: {address['name']}")
                        
                        # Extract postcode for targeted search
                        postcode = extract_postcode(address['address'])
                        if postcode:
                            # Update campaign postcode for this search
                            campaign.postcode = postcode
                            campaign.distance_miles = 25  # Smaller radius for address-based search
                            db.session.commit()
                            
                            # Generate leads for this specific location
                            service.generate_leads(campaign.id)
                        else:
                            print(f"[ADDRESS CAMPAIGN] No postcode found for {address['name']}")
                    
                    # Mark campaign as completed
                    campaign.status = LeadGenerationStatus.COMPLETED
                    campaign.completed_at = datetime.utcnow()
                    db.session.commit()
                    
                    print(f"[ADDRESS CAMPAIGN] Campaign {campaign.id} completed successfully")
                    
                except Exception as e:
                    print(f"[ADDRESS CAMPAIGN] Error in campaign {campaign.id}: {str(e)}")
                    campaign.status = LeadGenerationStatus.FAILED
                    campaign.completed_at = datetime.utcnow()
                    db.session.commit()
        
        # Start background thread
        import threading
        thread = threading.Thread(target=run_address_campaign, daemon=True)
        thread.start()
        
        print(f"[ADDRESS CAMPAIGN] Created campaign {campaign.id}: {campaign_name}")
        
        return jsonify({
            'success': True,
            'message': 'Address-based campaign created successfully',
            'campaign_id': campaign.id,
            'campaign_name': campaign_name
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[ADDRESS CAMPAIGN] Error creating campaign: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_generation_bp.route('/campaigns')
@login_required
def list_campaigns():
    """List all lead generation campaigns"""
    campaigns = LeadGenerationCampaign.query.filter_by(created_by=current_user.id)\
        .order_by(desc(LeadGenerationCampaign.created_at)).all()
    
    return render_template('lead_generation/campaigns_list.html', campaigns=campaigns)

@lead_generation_bp.route('/campaigns/new', methods=['GET', 'POST'])
@login_required
def create_campaign():
    """Create new lead generation campaign"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            campaign = LeadGenerationCampaign(
                name=data['name'],
                description=data.get('description'),
                prompt_type=data['prompt_type'],
                custom_prompt=data.get('custom_prompt'),
                postcode=data['postcode'],
                distance_miles=int(data.get('distance_miles', 20)),
                max_results=int(data.get('max_results', 100)),
                company_name_filter=data.get('company_name_filter'),
                include_existing_customers=bool(data.get('include_existing_customers')),
                exclude_duplicates=bool(data.get('exclude_duplicates', True)),
                created_by=current_user.id
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'campaign_id': campaign.id,
                    'message': 'Campaign created successfully'
                })
            else:
                flash('Campaign created successfully', 'success')
                return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign.id))
                
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
            else:
                flash(f'Error creating campaign: {str(e)}', 'danger')
    
    return render_template('lead_generation/campaign_form.html', 
                         default_prompts=DEFAULT_PROMPTS)

@lead_generation_bp.route('/campaigns/<int:campaign_id>')
@login_required
def view_campaign(campaign_id):
    """View campaign details and leads"""
    campaign = LeadGenerationCampaign.query.get_or_404(campaign_id)
    
    # Get leads for this campaign
    leads = Lead.query.filter_by(campaign_id=campaign_id)\
        .order_by(desc(Lead.lead_score), desc(Lead.created_at)).all()
    
    # Get campaign statistics
    stats = {
        'total_leads': len(leads),
        'new_leads': len([l for l in leads if l.status == LeadStatus.NEW]),
        'contacted_leads': len([l for l in leads if l.status == LeadStatus.CONTACTED]),
        'qualified_leads': len([l for l in leads if l.status == LeadStatus.QUALIFIED]),
        'converted_leads': len([l for l in leads if l.status == LeadStatus.CONVERTED]),
        'average_score': sum([l.lead_score for l in leads]) / len(leads) if leads else 0
    }
    
    # Get the actual prompt text used for this campaign
    from utils.lead_generation_service import LeadGenerationService
    service = LeadGenerationService()
    actual_prompt = service._build_lead_generation_prompt(campaign)
    
    return render_template('lead_generation/campaign_detail.html',
                         campaign=campaign,
                         leads=leads,
                         stats=stats,
                         actual_prompt=actual_prompt)


@lead_generation_bp.route('/campaigns/<int:campaign_id>/manual')
@login_required
def manual_campaign(campaign_id):
    """Manual AI prompt approach for lead generation"""
    campaign = LeadGenerationCampaign.query.get_or_404(campaign_id)
    
    # Get the prompt for this campaign
    from utils.lead_generation_service import LeadGenerationService
    service = LeadGenerationService()
    ai_prompt = service._build_lead_generation_prompt(campaign)
    
    return render_template('lead_generation/manual_campaign.html',
                         campaign=campaign,
                         ai_prompt=ai_prompt)


@lead_generation_bp.route('/campaigns/<int:campaign_id>/process-results', methods=['POST'])
@login_required
def process_manual_results(campaign_id):
    """Process manually pasted AI results"""
    campaign = LeadGenerationCampaign.query.get_or_404(campaign_id)
    
    try:
        # Get the pasted results from the form
        ai_results = request.form.get('ai_results', '').strip()
        
        if not ai_results:
            flash('Please paste the AI results before processing.', 'warning')
            return redirect(url_for('lead_generation.manual_campaign', campaign_id=campaign_id))
        
        # Process the results using the existing service
        from utils.lead_generation_service import LeadGenerationService
        service = LeadGenerationService()
        
        # Parse the AI response
        leads_data = service._parse_ai_response(ai_results, campaign)
        
        # Process and validate leads
        processed_leads = service._process_leads_data(leads_data, campaign)
        
        # Create lead records
        leads_result = service.create_leads_from_campaign(campaign, processed_leads)
        
        # Update campaign statistics
        campaign.total_found = len(processed_leads)
        campaign.leads_created = leads_result['leads_created']
        campaign.duplicates_found = leads_result['duplicates_found']
        campaign.status = LeadGenerationStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()
        campaign.ai_analysis_summary = ai_results
        
        db.session.commit()
        
        flash(f'Successfully processed {len(processed_leads)} leads! Created {leads_result["leads_created"]} new leads, {leads_result["duplicates_found"]} duplicates found.', 'success')
        return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing results: {str(e)}', 'danger')
        return redirect(url_for('lead_generation.manual_campaign', campaign_id=campaign_id))

@lead_generation_bp.route('/campaigns/<int:campaign_id>/run', methods=['GET', 'POST'])
@login_required
def run_campaign(campaign_id):
    """Run lead generation campaign"""
    campaign = LeadGenerationCampaign.query.get_or_404(campaign_id)
    
    # Allow re-running completed or failed campaigns
    if campaign.status == LeadGenerationStatus.RUNNING:
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'Campaign is already running'
            }), 400
        else:
            flash('Campaign is already running', 'warning')
            return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign_id))
    
    try:
        # Reset campaign status for re-running
        campaign.status = LeadGenerationStatus.DRAFT
        campaign.started_at = None
        campaign.completed_at = None
        campaign.total_found = 0
        campaign.leads_created = 0
        campaign.duplicates_found = 0
        
        # Clear existing leads for this campaign (optional - you might want to keep them)
        existing_leads = Lead.query.filter_by(campaign_id=campaign_id).all()
        for lead in existing_leads:
            db.session.delete(lead)
        
        # Commit the reset and deletions immediately to avoid lock
        db.session.commit()
        
        print(f"Campaign reset complete, starting lead generation...")
        
        # Update status to RUNNING immediately
        campaign.status = LeadGenerationStatus.RUNNING
        campaign.started_at = datetime.utcnow()
        db.session.commit()
        
        # Start campaign in separate process (survives Flask reloads!)
        python_exe = sys.executable
        worker_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'campaign_worker.py')
        
        # Start the worker process in background
        subprocess.Popen(
            [python_exe, worker_script, str(campaign_id)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        print(f"[OK] Campaign {campaign_id} started in separate process")
        
        message = 'Campaign started! It will run in the background and may take 3-5 minutes to complete.'
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': message,
                'campaign_id': campaign_id
            })
        else:
            flash(message, 'success')
            return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign_id))
            
    except Exception as e:
        db.session.rollback()
        
        # Update campaign status to FAILED
        campaign.status = LeadGenerationStatus.FAILED
        campaign.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Log the full error
        import traceback
        print(f"[ERROR] Campaign {campaign_id} failed with error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        error_msg = f'Campaign failed: {str(e)}'
        if request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign_id))

@lead_generation_bp.route('/campaigns/<int:campaign_id>/stop', methods=['POST'])
@login_required
def stop_campaign(campaign_id):
    """Stop a running campaign"""
    campaign = LeadGenerationCampaign.query.get_or_404(campaign_id)
    
    if campaign.status != LeadGenerationStatus.RUNNING:
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'Campaign is not currently running'
            }), 400
        else:
            flash('Campaign is not currently running.', 'warning')
            return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign_id))
    
    try:
        # Update campaign status to cancelled
        campaign.status = LeadGenerationStatus.CANCELLED
        campaign.completed_at = datetime.utcnow()
        db.session.commit()
        
        message = f'Campaign "{campaign.name}" has been stopped.'
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': message,
                'campaign_id': campaign_id
            })
        else:
            flash(message, 'success')
            return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign_id))
            
    except Exception as e:
        db.session.rollback()
        
        error_msg = f'Failed to stop campaign: {str(e)}'
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('lead_generation.view_campaign', campaign_id=campaign_id))

@lead_generation_bp.route('/leads/<int:lead_id>/convert')
@login_required
def convert_lead_to_customer(lead_id):
    """Convert a lead to a CRM customer"""
    lead = Lead.query.get_or_404(lead_id)
    
    try:
        # Create new customer from lead data
        from models_crm import Customer, CustomerStatus, Contact
        
        # Validate website URL - only set if it looks like a URL, not an address
        website_url = None
        if lead.website and lead.website.strip():
            # Check if it looks like a URL (starts with http/https) or is clearly an address
            website = lead.website.strip()
            if website.startswith(('http://', 'https://', 'www.')):
                website_url = website
            elif not any(word in website.lower() for word in ['street', 'road', 'avenue', 'lane', 'close', 'drive', 'place', 'uk', 'postcode', 'postal']):
                # If it doesn't contain address keywords, treat as potential URL
                website_url = website
        
        customer = Customer(
            company_name=lead.company_name,
            status=CustomerStatus.LEAD,  # Start as lead so AI analysis can be run
            business_sector=map_business_sector_to_enum(lead.business_sector),
            business_size_category=lead.company_size,  # Map company_size to business_size_category
            website=website_url,  # Use validated website URL
            company_registration=lead.company_registration,
            registration_confirmed=lead.registration_confirmed,
            billing_address=lead.address,
            billing_postcode=lead.postcode,
            ai_analysis_raw=json.dumps(lead.ai_analysis) if lead.ai_analysis else None,
            linkedin_url=lead.linkedin_url,
            linkedin_data=json.dumps(lead.linkedin_data) if lead.linkedin_data else None,
            companies_house_data=json.dumps(lead.companies_house_data) if lead.companies_house_data else None,
            website_data=json.dumps(lead.website_data) if lead.website_data else None,
            created_by=current_user.id
        )
        
        db.session.add(customer)
        db.session.flush()  # Get the customer ID
        
        # Create contact if we have contact information
        if lead.contact_name or lead.contact_email or lead.contact_phone:
            # Parse contact name into first and last name
            contact_name = lead.contact_name or 'Unknown Contact'
            name_parts = contact_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            contact = Contact(
                customer_id=customer.id,
                first_name=first_name,
                last_name=last_name,
                email=lead.contact_email,
                phone=lead.contact_phone,
                job_title=lead.contact_title,
                role=ContactRole.DECISION_MAKER  # Default role
            )
            db.session.add(contact)
        
        # Update lead to mark as converted
        lead.status = LeadStatus.CONVERTED
        lead.converted_to_customer_id = customer.id
        lead.conversion_date = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Lead "{lead.company_name}" successfully converted to CRM customer!', 'success')
        return redirect(url_for('crm.view_customer', customer_id=customer.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error converting lead: {str(e)}', 'danger')
        return redirect(url_for('lead_generation.view_campaign', campaign_id=lead.campaign_id))

@lead_generation_bp.route('/leads')
@login_required
def list_leads():
    """List all leads"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    campaign_filter = request.args.get('campaign', 'all')
    
    query = Lead.query.join(LeadGenerationCampaign)\
        .filter(LeadGenerationCampaign.created_by == current_user.id)
    
    if status_filter != 'all':
        query = query.filter(Lead.status == status_filter)
    
    if campaign_filter != 'all':
        query = query.filter(Lead.campaign_id == campaign_filter)
    
    leads = query.order_by(desc(Lead.lead_score), desc(Lead.created_at))\
        .paginate(page=page, per_page=50, error_out=False)
    
    # Get campaigns for filter dropdown
    campaigns = LeadGenerationCampaign.query.filter_by(created_by=current_user.id).all()
    
    return render_template('lead_generation/leads_list.html',
                         leads=leads,
                         campaigns=campaigns,
                         status_filter=status_filter,
                         campaign_filter=campaign_filter)

@lead_generation_bp.route('/all-leads')
@login_required
def view_all_leads():
    """Comprehensive view of all leads across all campaigns with advanced filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Build query with joins for campaign and conversion data
    leads_query = db.session.query(Lead, LeadGenerationCampaign).join(
        LeadGenerationCampaign, Lead.campaign_id == LeadGenerationCampaign.id
    ).order_by(desc(Lead.created_at))
    
    # Advanced filtering options
    campaign_id = request.args.get('campaign_id', type=int)
    status_filter = request.args.get('status')
    sector_filter = request.args.get('sector')
    score_min = request.args.get('score_min', type=int)
    score_max = request.args.get('score_max', type=int)
    search_term = request.args.get('search', '').strip()
    
    # Apply filters
    if campaign_id:
        leads_query = leads_query.filter(Lead.campaign_id == campaign_id)
    
    if status_filter:
        leads_query = leads_query.filter(Lead.status == LeadStatus[status_filter.upper()])
    
    if sector_filter:
        leads_query = leads_query.filter(Lead.business_sector.ilike(f'%{sector_filter}%'))
    
    if score_min is not None:
        leads_query = leads_query.filter(Lead.lead_score >= score_min)
    
    if score_max is not None:
        leads_query = leads_query.filter(Lead.lead_score <= score_max)
    
    if search_term:
        leads_query = leads_query.filter(
            or_(
                Lead.company_name.ilike(f'%{search_term}%'),
                Lead.contact_name.ilike(f'%{search_term}%'),
                Lead.contact_email.ilike(f'%{search_term}%'),
                Lead.business_sector.ilike(f'%{search_term}%')
            )
        )
    
    # Paginate results
    leads_pagination = leads_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options
    campaigns = LeadGenerationCampaign.query.order_by(desc(LeadGenerationCampaign.created_at)).all()
    
    # Get unique sectors for filter dropdown
    sectors = db.session.query(Lead.business_sector).distinct().filter(
        Lead.business_sector.isnot(None)
    ).order_by(Lead.business_sector).all()
    sectors = [s[0] for s in sectors if s[0]]
    
    # Get lead statistics
    total_leads = Lead.query.count()
    converted_leads = Lead.query.filter(Lead.status == LeadStatus.CONVERTED).count()
    qualified_leads = Lead.query.filter(Lead.status == LeadStatus.QUALIFIED).count()
    new_leads = Lead.query.filter(Lead.status == LeadStatus.NEW).count()
    
    # Get recent activity (last 7 days)
    recent_date = datetime.utcnow() - timedelta(days=7)
    recent_leads = Lead.query.filter(Lead.created_at >= recent_date).count()
    
    stats = {
        'total': total_leads,
        'converted': converted_leads,
        'qualified': qualified_leads,
        'new': new_leads,
        'recent': recent_leads
    }
    
    return render_template('lead_generation/all_leads.html',
                         leads=leads_pagination,
                         campaigns=campaigns,
                         sectors=sectors,
                         stats=stats,
                         filters={
                             'campaign_id': campaign_id,
                             'status': status_filter,
                             'sector': sector_filter,
                             'score_min': score_min,
                             'score_max': score_max,
                             'search': search_term
                         })

@lead_generation_bp.route('/leads/<int:lead_id>')
@login_required
def view_lead(lead_id):
    """View lead details"""
    lead = Lead.query.get_or_404(lead_id)
    
    # Check if this lead has already been converted to a customer
    if lead.converted_to_customer_id:
        # Lead has been converted, redirect to customer detail page
        from models_crm import Customer
        customer = Customer.query.get(lead.converted_to_customer_id)
        if customer:
            flash(f'This lead has already been converted to a customer.', 'info')
            return redirect(url_for('crm.view_customer', customer_id=customer.id))
    
    # Also check by company name as a fallback
    from models_crm import Customer
    existing_customer = Customer.query.filter_by(company_name=lead.company_name).first()
    
    if existing_customer:
        # Lead has already been converted, redirect to customer detail page
        flash(f'This lead has already been converted to a customer.', 'info')
        return redirect(url_for('crm.view_customer', customer_id=existing_customer.id))
    
    # Get lead interactions
    from models_lead_generation import LeadInteraction
    interactions = LeadInteraction.query.filter_by(lead_id=lead.id).order_by(desc(LeadInteraction.created_at)).all()
    
    return render_template('lead_generation/lead_detail.html',
                         lead=lead,
                         interactions=interactions)

@lead_generation_bp.route('/campaigns/api')
@login_required
def get_campaigns_api():
    """Get campaigns as JSON for API calls"""
    campaigns = LeadGenerationCampaign.query.filter_by(created_by=current_user.id).all()
    return jsonify([{
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'status': campaign.status.value
    } for campaign in campaigns])

def collect_competitor_data(campaign_id: int, competitor_names: list, source_company: str):
    """Collect detailed information about competitor companies"""
    try:
        from utils.external_data_service import ExternalDataService
        from utils.customer_intelligence import CustomerIntelligenceService
        
        external_service = ExternalDataService()
        intelligence_service = CustomerIntelligenceService()
        
        print(f"[COMPETITOR] Starting data collection for {len(competitor_names)} competitors")
        
        for i, company_name in enumerate(competitor_names):
            try:
                print(f"[COMPETITOR] Processing {i+1}/{len(competitor_names)}: {company_name}")
                
                # Get the lead for this competitor
                lead = Lead.query.filter_by(
                    campaign_id=campaign_id,
                    company_name=company_name
                ).first()
                
                if not lead:
                    print(f"[COMPETITOR] Lead not found for {company_name}")
                    continue
                
                # Get comprehensive external data (same as normal campaigns)
                print(f"[COMPETITOR] Getting comprehensive data for {company_name}")
                external_data = external_service.get_comprehensive_company_data(company_name)
                
                if external_data:
                    import json
                    
                    # Store all external data
                    lead.companies_house_data = json.dumps(external_data.get('companies_house', {}))
                    lead.linkedin_data = json.dumps(external_data.get('linkedin', {}))
                    lead.website_data = json.dumps(external_data.get('website', {}))
                    if external_data.get('google_maps'):
                        lead.google_maps_data = json.dumps(external_data['google_maps'])
                    
                    # Update lead with the best available data
                    web_data = external_data.get('website', {})
                    ch_data = external_data.get('companies_house', {})
                    
                    # Website
                    if web_data.get('website') and not lead.website:
                        lead.website = web_data['website']
                    
                    # Contact information
                    if web_data.get('contact_name') and not lead.contact_name:
                        lead.contact_name = web_data['contact_name']
                    if web_data.get('contact_email') and not lead.contact_email:
                        lead.contact_email = web_data['contact_email']
                    if web_data.get('contact_phone') and not lead.contact_phone:
                        lead.contact_phone = web_data['contact_phone']
                    
                    # Address information
                    if ch_data.get('address') and not lead.address:
                        lead.address = ch_data['address']
                    elif web_data.get('address') and not lead.address:
                        lead.address = web_data['address']
                    
                    if ch_data.get('postcode') and not lead.postcode:
                        lead.postcode = ch_data['postcode']
                    elif web_data.get('postcode') and not lead.postcode:
                        lead.postcode = web_data['postcode']
                    
                    # Business information
                    if ch_data.get('business_sector') and not lead.business_sector:
                        lead.business_sector = ch_data['business_sector']
                    elif web_data.get('business_sector') and not lead.business_sector:
                        lead.business_sector = web_data['business_sector']
                    
                    if ch_data.get('company_registration') and not lead.company_registration:
                        lead.company_registration = ch_data['company_registration']
                        lead.registration_confirmed = True
                    
                    # LinkedIn
                    if external_data.get('linkedin', {}).get('linkedin_url') and not lead.linkedin_url:
                        lead.linkedin_url = external_data['linkedin']['linkedin_url']
                    
                    print(f"[COMPETITOR] Updated {company_name} with external data")
                else:
                    print(f"[COMPETITOR] No external data found for {company_name}")
                
                # Run comprehensive AI analysis (same as normal campaigns)
                print(f"[COMPETITOR] Running AI analysis for {company_name}")
                ai_analysis = intelligence_service.analyze_company(
                    company_name=company_name,
                    website=lead.website,
                    external_data=external_data or {}
                )
                
                if ai_analysis and ai_analysis.get('success'):
                    analysis_data = ai_analysis.get('data', {})
                    lead.ai_analysis = json.dumps(analysis_data)
                    
                    # Update lead with AI analysis results
                    if analysis_data.get('business_sector') and not lead.business_sector:
                        lead.business_sector = analysis_data['business_sector']
                    if analysis_data.get('company_size') and not lead.company_size:
                        lead.company_size = analysis_data['company_size']
                    if analysis_data.get('lead_score'):
                        lead.lead_score = analysis_data['lead_score']
                    
                    # Set qualification reason and other fields
                    lead.qualification_reason = f"Competitor of {source_company}. {analysis_data.get('business_description', 'IT services company')}"
                    lead.timeline_estimate = "Ongoing monitoring"
                    if not lead.lead_score:
                        lead.lead_score = 75  # High score for competitors
                    
                    print(f"[COMPETITOR] AI analysis completed for {company_name}")
                else:
                    print(f"[COMPETITOR] AI analysis failed for {company_name}")
                    # Set basic fields if AI analysis fails
                    lead.qualification_reason = f"Competitor of {source_company}. IT services company"
                    lead.timeline_estimate = "Ongoing monitoring"
                    lead.lead_score = 75  # High score for competitors
                
                # Commit after each company to avoid losing progress
                db.session.commit()
                print(f"[COMPETITOR] Successfully processed {company_name}")
                
            except Exception as e:
                print(f"[COMPETITOR] Error processing {company_name}: {e}")
                continue
        
        print(f"[COMPETITOR] Completed data collection for campaign {campaign_id}")
        
    except Exception as e:
        print(f"[COMPETITOR] Error in competitor data collection: {e}")

def search_company_information(company_name: str) -> dict:
    """Search for detailed information about a specific company"""
    try:
        from utils.lead_generation_service import LeadGenerationService
        service = LeadGenerationService()
        
        # Use AI to search for specific company information
        prompt = f"""
        I need detailed information about this specific UK company: "{company_name}"
        
        Please search for and provide:
        1. Company website URL
        2. Contact information (name, email, phone)
        3. Business address and postcode
        4. Business sector/industry
        5. Company size (employees)
        6. Company registration number (if available)
        7. LinkedIn company page URL
        8. Brief description of services
        9. Estimated annual revenue (if possible)
        
        Focus on finding the OFFICIAL company information, not generic listings.
        Look for their actual website, contact details, and business information.
        
        Respond in JSON format:
        {{
            "website": "string",
            "contact_name": "string", 
            "contact_email": "string",
            "contact_phone": "string",
            "address": "string",
            "postcode": "string",
            "business_sector": "string",
            "company_size": "string",
            "company_registration": "string",
            "linkedin_url": "string",
            "description": "string",
            "estimated_revenue": "string"
        }}
        """
        
        # Use the AI service to search for company information
        response = service._use_responses_api_with_web_search(prompt)
        
        if response:
            # Try to parse JSON from the response
            try:
                import json
                # Extract JSON from the response
                if hasattr(response, 'results') and response.results:
                    content = response.results[0].content
                    if isinstance(content, list) and len(content) > 0:
                        text = content[0].text
                    else:
                        text = str(content)
                else:
                    text = str(response)
                
                # Find JSON in the response
                start_idx = text.find('{')
                end_idx = text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = text[start_idx:end_idx]
                    return json.loads(json_str)
                
            except Exception as e:
                print(f"[COMPETITOR] Error parsing JSON for {company_name}: {e}")
        
        return None
        
    except Exception as e:
        print(f"[COMPETITOR] Error searching for {company_name}: {e}")
        return None

@lead_generation_bp.route('/create-competitors-campaign', methods=['POST'])
@login_required
def create_competitors_campaign():
    """Create a new campaign specifically for competitor companies and auto-run it"""
    try:
        data = request.get_json()
        competitor_text = data.get('competitors_text', '')
        source_company = data.get('source_company', 'Unknown Company')
        
        if not competitor_text:
            return jsonify({'success': False, 'error': 'Missing competitors text'})
        
        # Parse competitor companies from the text
        import re
        
        def is_valid_company_name(name):
            """Validate that a name is likely a real company, not a location or generic term"""
            name_lower = name.lower().strip()
            
            # Exclude common non-company terms
            invalid_terms = [
                'derby', 'sheffield', 'nottingham', 'leicester', 'birmingham', 'manchester',
                'liverpool', 'leeds', 'bristol', 'newcastle', 'north', 'south', 'east', 'west',
                'regional', 'national', 'local', 'area', 'region', 'county', 'city', 'town',
                'high', 'low', 'central', 'north west', 'south east', 'south west', 'midlands',
                'england', 'scotland', 'wales', 'northern ireland', 'uk', 'britain'
            ]
            
            # Must not be in invalid terms
            if name_lower in invalid_terms:
                return False
            
            # Must be at least 3 characters
            if len(name) < 3:
                return False
            
            # Must contain at least one letter
            if not re.search(r'[a-zA-Z]', name):
                return False
            
            # Should not be just numbers or single words without company indicators
            words = name.split()
            if len(words) == 1 and not any(suffix in name_lower for suffix in ['ltd', 'limited', 'plc', 'inc', 'corp', 'llc', 'llp']):
                return False
            
            return True
        
        # Extract company names (improved patterns)
        company_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Ltd|Limited|PLC|plc|Inc|Corp|LLC|LLP|Group|Holdings|Solutions|Services|Systems)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:IT|Computing|Technology|Systems|Solutions|Group|Services)\b',
            r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Digital|Managed|Cloud|Data|Network|Software|Hardware|Support|Consulting))\b'
        ]
        
        # Known competitor companies from the example
        known_competitors = [
            'Air IT', 'BCN Group', 'Littlefish', 'Razorblue', 'SysGroup', 
            'Node4', 'Redcentric', 'Digital Space', 'Timico', 'ANS Group', 
            'Claranet', 'Phoenix', 'fluidone', 'M247', 'Mirus IT', 'Highlander Computing Solutions'
        ]
        
        competitors = set()
        
        # First, look for known competitors
        for competitor in known_competitors:
            if competitor.lower() in competitor_text.lower():
                competitors.add(competitor)
        
        # Then extract using patterns with validation
        for pattern in company_patterns:
            matches = re.findall(pattern, competitor_text)
            for match in matches:
                company_name = match.strip()
                if is_valid_company_name(company_name) and company_name not in competitors:
                    competitors.add(company_name)
        
        if not competitors:
            return jsonify({'success': False, 'error': 'No competitor companies found in the text'})
        
        # Create campaign name with date and time
        from datetime import datetime
        now = datetime.now()
        campaign_name = f"Competitors of {source_company} - {now.strftime('%Y-%m-%d %H:%M')}"
        
        # Create new campaign specifically for competitors
        campaign = LeadGenerationCampaign(
            name=campaign_name,
            description=f"Competitive intelligence campaign for {source_company}. Automatically generated from AI competitor analysis.",
            prompt_type='competitor_verification',
            postcode="LE1 1AA",  # Default Leicester postcode
            distance_miles=100,  # Wide search area for competitors
            max_results=len(competitors) * 2,  # Allow some buffer
            created_by=current_user.id,
            status=LeadGenerationStatus.DRAFT,
            custom_search_criteria=f"COMPETITORS TO VERIFY: {', '.join(sorted(competitors))}"
        )
        
        db.session.add(campaign)
        db.session.flush()  # Get campaign ID
        
        # Create leads for each competitor
        created_leads = []
        for company_name in competitors:
            # Check if lead already exists within this campaign first
            existing_lead_in_campaign = Lead.query.filter_by(
                campaign_id=campaign.id,
                company_name=company_name
            ).first()
            
            if existing_lead_in_campaign:
                print(f"[COMPETITOR DEDUP] Skipping duplicate in same campaign: {company_name}")
                continue
            
            # Check if lead already exists across all campaigns (deduplication)
            existing_lead_anywhere = Lead.query.filter_by(
                company_name=company_name,
                created_by=current_user.id
            ).first()
            
            # Also check if company already exists as a customer in CRM
            from models_crm import Customer
            existing_customer = Customer.query.filter_by(company_name=company_name).first()
            
            if existing_lead_anywhere:
                print(f"[COMPETITOR DEDUP] Skipping - already exists as lead: {company_name}")
                continue
                
            if existing_customer:
                print(f"[COMPETITOR DEDUP] Skipping - already exists as customer: {company_name}")
                continue
            
            if not existing_lead_anywhere and not existing_customer:
                # Create new lead for competitor
                lead = Lead(
                    campaign_id=campaign.id,
                    company_name=company_name,
                    status=LeadStatus.NEW,
                    source=LeadSource.AI_GENERATED,
                    qualification_reason=f"Competitor of {source_company} identified through AI analysis",
                    timeline_estimate="Unknown",
                    created_by=current_user.id
                )
                
                db.session.add(lead)
                created_leads.append(company_name)
        
        # Set campaign status to RUNNING and start processing
        campaign.status = LeadGenerationStatus.RUNNING
        db.session.commit()
        
        # Start the campaign in background to collect detailed data
        try:
            # Run competitor data collection in background thread
            import threading
            def run_competitor_campaign():
                try:
                    # Use specialized competitor data collection instead of general lead generation
                    collect_competitor_data(campaign.id, created_leads, source_company)
                    
                    # Update campaign status
                    with current_app.app_context():
                        campaign.status = LeadGenerationStatus.COMPLETED
                        campaign.leads_created = len(created_leads)
                        db.session.commit()
                except Exception as e:
                    with current_app.app_context():
                        campaign.status = LeadGenerationStatus.FAILED
                        db.session.commit()
                    print(f"Competitor campaign failed: {e}")
            
            thread = threading.Thread(target=run_competitor_campaign, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"Error starting competitor campaign: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Created competitor campaign with {len(created_leads)} companies',
            'campaign_id': campaign.id,
            'campaign_name': campaign_name,
            'competitors_added': created_leads,
            'total_competitors': len(competitors)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@lead_generation_bp.route('/leads/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    """Perform bulk actions on selected leads"""
    try:
        data = request.get_json()
        action = data.get('action')
        lead_ids = data.get('lead_ids', [])
        
        if not lead_ids:
            return jsonify({
                'success': False,
                'error': 'No leads selected'
            }), 400
        
        leads = Lead.query.filter(Lead.id.in_(lead_ids),
                                 Lead.campaign.has(created_by=current_user.id)).all()
        
        if action == 'convert_to_customers':
            customers_created = 0
            for lead in leads:
                if lead.status != LeadStatus.CONVERTED:
                    customer = Customer(
                        company_name=lead.company_name,
                        website=lead.website,
                        company_registration=lead.company_registration,
                        main_phone=lead.contact_phone,
                        main_email=lead.contact_email,
                        billing_address=lead.address,
                        source='Lead Generation',
                        status=CustomerStatus.LEAD,
                        created_by=current_user.id
                    )
                    db.session.add(customer)
                    db.session.flush()
                    
                    lead.status = LeadStatus.CONVERTED
                    lead.converted_to_customer_id = customer.id
                    lead.conversion_date = datetime.utcnow()
                    customers_created += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully converted {customers_created} leads to customers'
            })
        
        elif action == 'mark_contacted':
            for lead in leads:
                lead.status = LeadStatus.CONTACTED
                lead.last_contact_date = datetime.utcnow()
                lead.contact_attempts += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Marked {len(leads)} leads as contacted'
            })
        
        elif action == 'mark_qualified':
            for lead in leads:
                lead.status = LeadStatus.QUALIFIED
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Marked {len(leads)} leads as qualified'
            })
        
        elif action == 'mark_rejected':
            for lead in leads:
                lead.status = LeadStatus.REJECTED
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Marked {len(leads)} leads as rejected'
            })
        
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_generation_bp.route('/leads/<int:lead_id>/add-interaction', methods=['POST'])
@login_required
def add_interaction(lead_id):
    """Add interaction to lead"""
    lead = Lead.query.get_or_404(lead_id)
    
    try:
        data = request.get_json()
        
        from models_lead_generation import LeadInteraction
        
        interaction = LeadInteraction(
            lead_id=lead_id,
            interaction_type=data['interaction_type'],
            subject=data.get('subject'),
            summary=data['summary'],
            notes=data.get('notes'),
            outcome=data.get('outcome'),
            next_steps=data.get('next_steps'),
            follow_up_date=datetime.fromisoformat(data['follow_up_date']) if data.get('follow_up_date') else None,
            created_by=current_user.id
        )
        
        db.session.add(interaction)
        
        # Update lead status and contact info
        if data.get('outcome') == 'positive':
            lead.status = LeadStatus.QUALIFIED
        elif data.get('outcome') == 'negative':
            lead.status = LeadStatus.REJECTED
        
        lead.last_contact_date = datetime.utcnow()
        lead.contact_attempts += 1
        
        if data.get('follow_up_date'):
            lead.next_follow_up_date = datetime.fromisoformat(data['follow_up_date'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Interaction added successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
