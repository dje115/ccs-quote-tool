#!/usr/bin/env python3
"""
CRM routes for customer and contact management.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Quote
from models_crm import Customer, Contact, CustomerInteraction, BusinessSector, CustomerStatus, ContactRole
from utils.customer_intelligence import CustomerIntelligenceService
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import json

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/crm')
@login_required
def crm_dashboard():
    """CRM Dashboard"""
    return render_template('crm/dashboard.html')

@crm_bp.route('/customers')
@login_required
def list_customers():
    """List all customers"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Search and filter parameters
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    sector_filter = request.args.get('sector', '')
    
    # Build query
    query = Customer.query
    
    if search:
        query = query.filter(
            or_(
                Customer.company_name.ilike(f'%{search}%'),
                Customer.main_email.ilike(f'%{search}%'),
                Customer.primary_business_activities.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter(Customer.status == CustomerStatus(status_filter))
    
    if sector_filter:
        query = query.filter(Customer.business_sector == BusinessSector(sector_filter))
    
    customers = query.order_by(Customer.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crm/customers_list.html', 
                         customers=customers,
                         search=search,
                         status_filter=status_filter,
                         sector_filter=sector_filter,
                         business_sectors=BusinessSector,
                         customer_statuses=CustomerStatus)

@crm_bp.route('/customers/new', methods=['GET', 'POST'])
@login_required
def create_customer():
    """Create new customer"""
    if request.method == 'POST':
        try:
            # Check if request is JSON
            if request.is_json:
                data = request.get_json()
            else:
                # Handle form data
                data = request.form.to_dict()
            
            customer = Customer(
                company_name=data['name'],
                website=data.get('website'),
                company_registration=data.get('company_registration'),
                registration_confirmed=bool(data.get('company_registration')),  # Auto-confirm human entries
                main_phone=data.get('phone'),
                main_email=data.get('email'),
                billing_address=data.get('address'),
                source=data.get('source', 'Manual Entry'),
                created_by=current_user.id
            )
            
            db.session.add(customer)
            db.session.commit()
            
            # Return JSON response for AJAX requests
            if request.is_json:
                return jsonify({
                    'success': True,
                    'customer_id': customer.id,
                    'message': 'Customer created successfully'
                })
            else:
                # Redirect for form submissions
                flash('Customer created successfully', 'success')
                return redirect(url_for('crm.view_customer', customer_id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
            else:
                flash(f'Error creating customer: {str(e)}', 'danger')
                return redirect(url_for('crm.create_customer'))
    
    return render_template('crm/customer_form.html', 
                         business_sectors=BusinessSector,
                         customer_statuses=CustomerStatus)

@crm_bp.route('/customer/<int:customer_id>')
@login_required
def view_customer(customer_id):
    """Customer detail view"""
    customer = Customer.query.get_or_404(customer_id)
    
    # Get recent interactions
    recent_interactions = CustomerInteraction.query.filter_by(customer_id=customer_id)\
        .order_by(CustomerInteraction.interaction_date.desc()).limit(10).all()
    
    # Get related quotes
    quotes = Quote.query.filter_by(customer_id=customer_id).order_by(Quote.created_at.desc()).limit(5).all()
    
    # Get contacts for this customer
    contacts = Contact.query.filter_by(customer_id=customer_id, is_active=True).order_by(Contact.is_primary.desc(), Contact.created_at).all()
    
    return render_template('crm/customer_detail.html',
                         customer=customer,
                         contacts=contacts,
                         recent_interactions=recent_interactions,
                         quotes=quotes,
                         contact_roles=ContactRole)

@crm_bp.route('/customer/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    """Edit customer"""
    customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Update basic fields
            customer.company_name = data.get('company_name') or data.get('name')
            customer.website = data.get('website')
            
            # Handle company registration - if human enters it, mark as confirmed
            new_registration = data.get('company_registration')
            if new_registration and new_registration != customer.company_registration:
                customer.company_registration = new_registration
                customer.registration_confirmed = True  # Human entry = confirmed
            
            customer.main_phone = data.get('main_phone')
            customer.main_email = data.get('main_email')
            customer.billing_address = data.get('billing_address')
            customer.billing_postcode = data.get('billing_postcode')
            customer.shipping_address = data.get('shipping_address')
            customer.shipping_postcode = data.get('shipping_postcode')
            customer.source = data.get('source')
            
            if data.get('status'):
                status_value = data.get('status').lower()
                customer.status = CustomerStatus(status_value)
            
            if data.get('business_sector'):
                customer.business_sector = BusinessSector(data['business_sector'])
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True})
            else:
                flash('Customer updated successfully', 'success')
                return redirect(url_for('crm.view_customer', customer_id=customer_id))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
            else:
                flash(f'Error updating customer: {str(e)}', 'danger')
                return redirect(url_for('crm.edit_customer', customer_id=customer_id))
    
    return render_template('crm/customer_edit.html',
                         customer=customer,
                         business_sectors=BusinessSector,
                         customer_statuses=CustomerStatus)

@crm_bp.route('/customers/<int:id>/ai-analysis', methods=['POST'])
@login_required
def run_ai_analysis(id):
    """Run AI analysis on customer"""
    try:
        customer = Customer.query.get_or_404(id)
        
        intelligence_service = CustomerIntelligenceService()
        result = intelligence_service.enhance_customer_with_ai(customer)
        
        if result.get('success'):
            # Check if a new company registration was found from external data (not AI analysis)
            newly_found_registration = None
            # Only suggest new registration if:
            # 1. No registration exists, OR
            # 2. Registration exists but is NOT human-confirmed (AI-found)
            # AND it comes from external data (Companies House), not AI analysis
            if (not customer.company_registration or not customer.registration_confirmed):
                # Check external data for real Companies House registration
                if result.get('external_data', {}).get('companies_house', {}).get('company_number'):
                    newly_found_registration = result['external_data']['companies_house']['company_number']
            
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'AI analysis completed successfully',
                'analysis': result['analysis'],
                'newly_found_company_registration': newly_found_registration
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI analysis failed')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/customers/<int:id>/technology-recommendations', methods=['GET'])
@login_required
def get_technology_recommendations(id):
    """Get technology recommendations for customer"""
    try:
        customer = Customer.query.get_or_404(id)
        
        intelligence_service = CustomerIntelligenceService()
        result = intelligence_service.suggest_technology_solutions(customer)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'recommendations': result['recommendations']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to generate recommendations')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/customers/<int:id>/contacts/new', methods=['GET', 'POST'])
@login_required
def new_contact(id):
    """Add new contact to customer"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Convert checkbox value to boolean (HTML sends 'on' for checked checkboxes)
            is_primary_raw = data.get('is_primary', False)
            is_primary = (is_primary_raw == 'on' or is_primary_raw is True) or len(customer.contacts) == 0
            
            # If setting as primary, unset other primary contacts
            if is_primary:
                for contact in customer.contacts:
                    contact.is_primary = False
            
            contact = Contact(
                customer_id=id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                job_title=data.get('job_title'),
                department=data.get('department'),
                role=ContactRole(data.get('role', 'general')),
                email=data.get('email'),
                phone=data.get('phone'),
                email_secondary=data.get('email_secondary'),
                phone_secondary=data.get('phone_secondary'),
                primary_email=data.get('primary_email', 'primary'),
                primary_phone=data.get('primary_phone', 'primary'),
                preferred_contact_method=data.get('preferred_contact_method'),
                preferred_contact_time=data.get('preferred_contact_time'),
                notes=data.get('notes'),
                is_primary=is_primary,
                is_active=True,
                created_by=current_user.id
            )
            
            db.session.add(contact)
            db.session.commit()
            
            # Return appropriate response based on request type
            if request.is_json:
                return jsonify({
                    'success': True,
                    'contact_id': contact.id,
                    'message': 'Contact added successfully'
                })
            else:
                flash('Contact added successfully', 'success')
                return redirect(url_for('crm.view_customer', customer_id=id))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
            else:
                flash(f'Error adding contact: {str(e)}', 'danger')
                return redirect(url_for('crm.new_contact', id=id))
    
    return render_template('crm/contact_form.html',
                         customer=customer,
                         contact_roles=ContactRole)

@crm_bp.route('/crm/customers/<int:customer_id>/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(customer_id, contact_id):
    """Edit contact"""
    contact = Contact.query.filter_by(id=contact_id, customer_id=customer_id).first_or_404()
    customer = contact.customer
    
    if request.method == 'GET':
        return render_template('crm/contact_form.html',
                             customer=customer,
                             contact=contact,
                             contact_roles=ContactRole)
    
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Update fields
        contact.first_name = data['first_name']
        contact.last_name = data['last_name']
        contact.job_title = data.get('job_title')
        contact.department = data.get('department')
        contact.role = ContactRole(data.get('role', 'general'))
        contact.email = data.get('email')
        contact.phone = data.get('phone')
        contact.email_secondary = data.get('email_secondary')
        contact.phone_secondary = data.get('phone_secondary')
        contact.primary_email = data.get('primary_email', 'primary')
        contact.primary_phone = data.get('primary_phone', 'primary')
        contact.preferred_contact_method = data.get('preferred_contact_method')
        contact.preferred_contact_time = data.get('preferred_contact_time')
        contact.notes = data.get('notes')
        
        # Handle primary contact logic (convert checkbox value to boolean)
        is_primary_raw = data.get('is_primary', False)
        is_primary = (is_primary_raw == 'on' or is_primary_raw is True)
        
        if is_primary and not contact.is_primary:
            # Unset other primary contacts
            for other_contact in contact.customer.contacts:
                if other_contact.id != contact.id:
                    other_contact.is_primary = False
            contact.is_primary = True
        
        db.session.commit()
        
        # Return appropriate response based on request type
        if request.is_json:
            return jsonify({'success': True})
        else:
            flash('Contact updated successfully', 'success')
            return redirect(url_for('crm.view_customer', customer_id=customer_id))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        else:
            flash(f'Error updating contact: {str(e)}', 'danger')
            return redirect(url_for('crm.view_customer', customer_id=customer_id))

@crm_bp.route('/customers/<int:customer_id>/toggle-registration-confirmation', methods=['POST'])
@login_required
def toggle_registration_confirmation(customer_id):
    """Toggle registration confirmation status"""
    customer = Customer.query.get_or_404(customer_id)
    
    try:
        data = request.get_json()
        confirmed = data.get('confirmed', False)
        
        customer.registration_confirmed = confirmed
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Registration confirmation {"enabled" if confirmed else "disabled"}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/customers/<int:customer_id>/update-registration', methods=['POST'])
@login_required
def update_company_registration(customer_id):
    """Update company registration number after AI confirmation"""
    customer = Customer.query.get_or_404(customer_id)
    
    try:
        data = request.get_json()
        new_registration = data.get('company_registration')
        
        if not new_registration:
            return jsonify({
                'success': False,
                'error': 'Company registration number is required'
            }), 400
        
        customer.company_registration = new_registration
        customer.registration_confirmed = False  # AI-found = not confirmed yet
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Company registration updated to {new_registration}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/customers/<int:customer_id>/change-status', methods=['POST'])
@login_required
def change_customer_status(customer_id):
    """Change customer status (lead/prospect/active/inactive/former)"""
    customer = Customer.query.get_or_404(customer_id)
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        new_status = data.get('status')
        
        if new_status not in [status.value for status in CustomerStatus]:
            return jsonify({
                'success': False,
                'error': 'Invalid status'
            }), 400
        
        customer.status = CustomerStatus(new_status)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'Customer status changed to {new_status}',
                'new_status': new_status
            })
        else:
            flash(f'Customer status changed to {new_status}', 'success')
            return redirect(url_for('crm.view_customer', customer_id=customer_id))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        else:
            flash(f'Error changing status: {str(e)}', 'danger')
            return redirect(url_for('crm.view_customer', customer_id=customer_id))

@crm_bp.route('/crm/customers/<int:customer_id>/interactions/new', methods=['POST'])
@login_required
def new_interaction(customer_id):
    """Add new interaction"""
    customer = Customer.query.get_or_404(customer_id)
    
    try:
        data = request.get_json()
        
        interaction = CustomerInteraction(
            customer_id=customer_id,
            contact_id=data.get('contact_id'),
            interaction_type=data['interaction_type'],
            subject=data['subject'],
            description=data.get('description'),
            outcome=data.get('outcome'),
            follow_up_required=data.get('follow_up_required', False),
            follow_up_date=datetime.fromisoformat(data['follow_up_date']) if data.get('follow_up_date') else None,
            created_by=current_user.id
        )
        
        db.session.add(interaction)
        
        # Update customer's last contact date
        customer.last_contact_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'interaction_id': interaction.id,
            'message': 'Interaction recorded successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/customers/search')
@login_required
def search_customers():
    """Search customers for autocomplete"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify({'customers': []})
    
    customers = Customer.query.filter(
        Customer.company_name.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.company_name,
            'business_sector': customer.business_sector.value if customer.business_sector else None,
            'lead_score': customer.lead_score,
            'status': customer.status.value if customer.status else None
        })
    
    return jsonify({'customers': results})

@crm_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Get CRM dashboard statistics"""
    try:
        # Basic counts
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter(Customer.status == CustomerStatus.ACTIVE).count()
        prospects = Customer.query.filter(Customer.status == CustomerStatus.PROSPECT).count()
        
        # Recent activity
        recent_interactions = CustomerInteraction.query.filter(
            CustomerInteraction.interaction_date >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Follow-ups needed
        follow_ups_needed = CustomerInteraction.query.filter(
            and_(
                CustomerInteraction.follow_up_required == True,
                CustomerInteraction.follow_up_date <= datetime.utcnow()
            )
        ).count()
        
        # High-value prospects (lead score > 70)
        high_value_prospects = Customer.query.filter(
            and_(
                Customer.status == CustomerStatus.PROSPECT,
                Customer.lead_score > 70
            )
        ).count()
        
        # Sector breakdown
        sector_counts = db.session.query(
            Customer.business_sector,
            db.func.count(Customer.id)
        ).group_by(Customer.business_sector).all()
        
        sector_breakdown = {
            sector.value if sector else 'Unknown': count 
            for sector, count in sector_counts
        }
        
        return jsonify({
            'success': True,
            'stats': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'prospects': prospects,
                'recent_interactions': recent_interactions,
                'follow_ups_needed': follow_ups_needed,
                'high_value_prospects': high_value_prospects,
                'sector_breakdown': sector_breakdown
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
