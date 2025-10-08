from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, send_file
from flask_login import login_required, current_user, login_user, logout_user, UserMixin
from models import db, User, Quote, Template, APISettings
from utils.ai_helper import AIHelper
from utils.pricing_helper import PricingHelper
from utils.document_generator import DocumentGenerator
from datetime import datetime
import json
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard"""
    recent_quotes = Quote.query.order_by(Quote.created_at.desc()).limit(5).all()
    total_quotes = Quote.query.count()
    
    return render_template('index.html', 
                         recent_quotes=recent_quotes, 
                         total_quotes=total_quotes)

@main_bp.route('/create-quote')
@login_required
def create_quote():
    """Quote creation form"""
    return render_template('create_quote.html')

@main_bp.route('/submit-quote', methods=['POST'])
@login_required
def submit_quote():
    """Process quote submission"""
    try:
        # Get form data
        data = request.get_json()
        
        # Generate quote number
        quote_count = Quote.query.count() + 1
        quote_number = f"CCS-{datetime.now().strftime('%Y%m%d')}-{quote_count:04d}"
        
        # Create quote record
        quote = Quote(
            quote_number=quote_number,
            client_name=data['client_name'],
            client_email=data.get('client_email'),
            client_phone=data.get('client_phone'),
            project_title=data['project_title'],
            project_description=data.get('project_description'),
            site_address=data['site_address'],
            building_type=data.get('building_type'),
            building_size=float(data.get('building_size', 0)) if data.get('building_size') else None,
            number_of_floors=int(data.get('number_of_floors', 1)),
            number_of_rooms=int(data.get('number_of_rooms', 1)),
            cabling_type=data.get('cabling_type'),
            wifi_requirements=bool(data.get('wifi_requirements')),
            cctv_requirements=bool(data.get('cctv_requirements')),
            door_entry_requirements=bool(data.get('door_entry_requirements')),
            special_requirements=data.get('special_requirements'),
            customer_id=int(data.get('customer_id')) if data.get('customer_id') else None,
            created_by=current_user.id
        )
        
        clarification_answers = data.get('clarification_answers') or []
        if clarification_answers:
            quote.clarifications_log = json.dumps(clarification_answers)
        
        db.session.add(quote)
        db.session.commit()
        
        pricing_helper = PricingHelper()
        
        # Use AI analysis data from frontend instead of re-running AI
        ai_analysis_record = data.get('ai_analysis_record', {})
        if ai_analysis_record:
            quote.ai_analysis = ai_analysis_record.get('analysis')
            quote.recommended_products = json.dumps(ai_analysis_record.get('products', []))
            quote.estimated_time = ai_analysis_record.get('estimated_time')
            quote.alternative_solutions = json.dumps(ai_analysis_record.get('alternatives', []))
            quote.labour_breakdown = json.dumps(ai_analysis_record.get('labour_breakdown', []))
            quote.quotation_details = json.dumps(ai_analysis_record.get('quotation', {}))
            quote.ai_raw_response = ai_analysis_record.get('ai_raw_response', '')  # Save complete raw AI response
            if ai_analysis_record.get('travel_distance_km'):
                quote.travel_distance_km = float(ai_analysis_record.get('travel_distance_km'))
            if ai_analysis_record.get('travel_time_minutes'):
                quote.travel_time_minutes = float(ai_analysis_record.get('travel_time_minutes'))
 
        pricing_data = pricing_helper.calculate_quote_pricing(quote)
        if pricing_data:
            quote.estimated_cost = pricing_data.get('total_cost')
            quote.quote_data = json.dumps(pricing_data)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'quote_id': quote.id,
            'quote_number': quote_number,
            'message': 'Quote created successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating quote: {str(e)}'
        }), 500

@main_bp.route('/quote/<int:quote_id>')
@login_required
def view_quote(quote_id):
    """View quote details"""
    quote = Quote.query.get_or_404(quote_id)
    
    # Parse JSON fields
    recommended_products = []
    alternative_solutions = []
    quote_data = {}
    
    if quote.recommended_products:
        recommended_products = json.loads(quote.recommended_products)
    if quote.alternative_solutions:
        alternative_solutions = json.loads(quote.alternative_solutions)
    if quote.quote_data:
        quote_data = json.loads(quote.quote_data)
    
    return render_template('view_quote.html', 
                         quote=quote,
                         recommended_products=recommended_products,
                         alternative_solutions=alternative_solutions,
                         quote_data=quote_data)

@main_bp.route('/quotes')
@login_required
def quotes_list():
    """List all quotes"""
    page = request.args.get('page', 1, type=int)
    quotes = Quote.query.order_by(Quote.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('quotes_list.html', quotes=quotes)

@main_bp.route('/generate-document/<int:quote_id>')
@login_required
def generate_document(quote_id):
    """Generate Word document for quote"""
    quote = Quote.query.get_or_404(quote_id)
    
    doc_generator = DocumentGenerator()
    file_path = doc_generator.generate_quote_document(quote)
    
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, 
                        download_name=f"{quote.quote_number}.docx")
    else:
        flash('Error generating document', 'error')
        return redirect(url_for('main.view_quote', quote_id=quote_id))

@main_bp.route('/send-quote/<int:quote_id>')
@login_required
def send_quote(quote_id):
    """Send quote via email"""
    quote = Quote.query.get_or_404(quote_id)
    
    # This would integrate with your email service
    # For now, just mark as sent
    quote.status = 'sent'
    db.session.commit()
    
    flash('Quote sent successfully', 'success')
    return redirect(url_for('main.view_quote', quote_id=quote_id))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('main.login'))
