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

@lead_generation_bp.route('/leads/<int:lead_id>/convert')
@login_required
def convert_lead_to_customer(lead_id):
    """Convert a lead to a CRM customer"""
    lead = Lead.query.get_or_404(lead_id)
    
    try:
        # Create new customer from lead data
        from models_crm import Customer, CustomerStatus, Contact
        
        customer = Customer(
            company_name=lead.company_name,
            status=CustomerStatus.LEAD,  # Start as lead so AI analysis can be run
            business_sector=map_business_sector_to_enum(lead.business_sector),
            business_size_category=lead.company_size,  # Map company_size to business_size_category
            website=lead.website,
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

@lead_generation_bp.route('/leads/<int:lead_id>')
@login_required
def view_lead(lead_id):
    """View lead details"""
    lead = Lead.query.get_or_404(lead_id)
    
    # Get lead interactions
    from models_lead_generation import LeadInteraction
    interactions = LeadInteraction.query.filter_by(lead_id=lead.id).order_by(desc(LeadInteraction.created_at)).all()
    
    return render_template('lead_generation/lead_detail.html',
                         lead=lead,
                         interactions=interactions)

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
