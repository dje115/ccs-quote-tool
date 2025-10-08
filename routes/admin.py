from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import (AdminSetting, APISettings, AIPrompt, AIPromptHistory, Quote, Template, User, db,
                    PricingItem, Category, Supplier)
from werkzeug.security import generate_password_hash
from utils.pricing_helper import PricingHelper
from utils.pricing_service import PricingService
import json
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
def admin_dashboard():
    """Admin dashboard"""
    stats = {
        'total_quotes': Quote.query.count(),
        'total_users': User.query.count(),
        'total_pricing_items': PricingItem.query.count(),
        'total_templates': Template.query.count()
    }
    
    recent_quotes = Quote.query.order_by(Quote.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_quotes=recent_quotes)

@admin_bp.route('/pricing')
def manage_pricing():
    """Manage pricing items"""
    pricing_items = PricingItem.query.all()
    return render_template('admin/pricing.html', pricing_items=pricing_items)

@admin_bp.route('/pricing/add', methods=['POST'])
def add_pricing_item():
    """Add new pricing item"""
    try:
        data = request.get_json()
        
        pricing_item = PricingItem(
            category=data['category'],
            subcategory=data.get('subcategory'),
            product_name=data['product_name'],
            description=data.get('description'),
            unit=data['unit'],
            cost_per_unit=float(data['cost_per_unit']),
            supplier=data.get('supplier'),
            part_number=data.get('part_number'),
            source='manual'
        )
        
        db.session.add(pricing_item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Pricing item added successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/pricing/import-excel', methods=['POST'])
def import_excel_pricing():
    """Import pricing from Excel file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Save file temporarily
        file_path = os.path.join('temp', file.filename)
        os.makedirs('temp', exist_ok=True)
        file.save(file_path)
        
        # Import using pricing helper
        pricing_helper = PricingHelper()
        imported_count = pricing_helper.import_excel_pricing(file_path)
        
        # Clean up temp file
        os.remove(file_path)
        
        return jsonify({
            'success': True, 
            'message': f'Imported {imported_count} pricing items'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/templates')
def manage_templates():
    """Manage quote templates"""
    templates = Template.query.all()
    return render_template('admin/templates.html', templates=templates)

@admin_bp.route('/templates/add', methods=['POST'])
def add_template():
    """Add new template"""
    try:
        data = request.get_json()
        
        template = Template(
            name=data['name'],
            template_type=data['template_type'],
            content=data['content'],
            variables=data.get('variables', '{}'),
            is_default=bool(data.get('is_default', False))
        )
        
        # If this is set as default, unset other defaults of the same type
        if template.is_default:
            Template.query.filter_by(
                template_type=template.template_type,
                is_default=True
            ).update({'is_default': False})
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Template added successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/ai-prompts')
def manage_ai_prompts():
    """Manage AI prompts"""
    prompts = AIPrompt.query.all()
    return render_template('admin/ai_prompts.html', prompts=prompts)

def _snapshot_prompt(prompt, note='Manual edit'):
    history = AIPromptHistory(
        prompt_id=prompt.id,
        prompt_type=prompt.prompt_type,
        name=prompt.name,
        description=prompt.description,
        system_prompt=prompt.system_prompt,
        user_prompt_template=prompt.user_prompt_template,
        variables=prompt.variables,
        note=note
    )
    db.session.add(history)


@admin_bp.route('/ai-prompts/add', methods=['POST'])
def add_ai_prompt():
    """Add new AI prompt"""
    try:
        data = request.get_json()
        
        prompt = AIPrompt(
            prompt_type=data['prompt_type'],
            name=data['name'],
            description=data.get('description', ''),
            system_prompt=data['system_prompt'],
            user_prompt_template=data['user_prompt_template'],
            variables=data.get('variables', '[]'),
            is_default=bool(data.get('is_default', False)),
            is_active=bool(data.get('is_active', True))
        )
        
        # If this is set as default, unset other defaults of the same type
        if prompt.is_default:
            AIPrompt.query.filter_by(
                prompt_type=prompt.prompt_type,
                is_default=True
            ).update({'is_default': False})
        
        db.session.add(prompt)
        db.session.commit()
        _snapshot_prompt(prompt, note='Initial creation')
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'AI prompt added successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/ai-prompts/<int:prompt_id>/edit', methods=['POST'])
def edit_ai_prompt(prompt_id):
    """Edit AI prompt"""
    try:
        prompt = AIPrompt.query.get_or_404(prompt_id)
        data = request.get_json()
        _snapshot_prompt(prompt, note='Before edit')

        prompt.name = data['name']
        prompt.description = data.get('description', '')
        prompt.system_prompt = data['system_prompt']
        prompt.user_prompt_template = data['user_prompt_template']
        prompt.variables = data.get('variables', '[]')
        prompt.is_default = bool(data.get('is_default', False))
        prompt.is_active = bool(data.get('is_active', True))
        
        # If this is set as default, unset other defaults of the same type
        if prompt.is_default:
            AIPrompt.query.filter_by(
                prompt_type=prompt.prompt_type,
                is_default=True
            ).filter(AIPrompt.id != prompt_id).update({'is_default': False})
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'AI prompt updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/ai-prompts/<int:prompt_id>/test', methods=['POST'])
def test_ai_prompt(prompt_id):
    """Test AI prompt with sample data"""
    try:
        prompt = AIPrompt.query.get_or_404(prompt_id)
        data = request.get_json()
        
        from utils.ai_helper import AIHelper
        ai_helper = AIHelper()
        
        # Test the prompt
        result = ai_helper.test_prompt(prompt.prompt_type, data.get('test_data', {}))
        
        return jsonify({
            'success': True, 
            'result': result,
            'message': 'Prompt test completed'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/ai-prompts/<int:prompt_id>')
def get_ai_prompt(prompt_id):
    """Get AI prompt data"""
    try:
        prompt = AIPrompt.query.get_or_404(prompt_id)
        
        return jsonify({
            'id': prompt.id,
            'prompt_type': prompt.prompt_type,
            'name': prompt.name,
            'description': prompt.description,
            'system_prompt': prompt.system_prompt,
            'user_prompt_template': prompt.user_prompt_template,
            'is_default': prompt.is_default,
            'is_active': prompt.is_active
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/ai-prompts/<int:prompt_id>/delete', methods=['POST'])
def delete_ai_prompt(prompt_id):
    """Delete AI prompt"""
    try:
        prompt = AIPrompt.query.get_or_404(prompt_id)
        db.session.delete(prompt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'AI prompt deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/ai-prompts/<prompt_type>/active')
def get_active_prompt(prompt_type):
    prompt = AIPrompt.query.filter_by(prompt_type=prompt_type, is_default=True, is_active=True).first()
    if not prompt:
        prompt = AIPrompt.query.filter_by(prompt_type=prompt_type, is_active=True).order_by(AIPrompt.updated_at.desc()).first()
    if not prompt:
        return jsonify({'success': False, 'message': 'No prompt found'}), 404
    return jsonify({
        'success': True,
        'prompt': {
            'id': prompt.id,
            'prompt_type': prompt.prompt_type,
            'name': prompt.name,
            'description': prompt.description,
            'system_prompt': prompt.system_prompt,
            'user_prompt_template': prompt.user_prompt_template,
            'is_default': prompt.is_default,
            'updated_at': prompt.updated_at.isoformat()
        }
    })


@admin_bp.route('/ai-prompts/<int:prompt_id>/history')
def get_prompt_history(prompt_id):
    history_entries = AIPromptHistory.query.filter_by(prompt_id=prompt_id).order_by(AIPromptHistory.created_at.desc()).all()
    return jsonify({
        'success': True,
        'history': [
            {
                'id': entry.id,
                'prompt_id': entry.prompt_id,
                'prompt_type': entry.prompt_type,
                'name': entry.name,
                'description': entry.description,
                'system_prompt': entry.system_prompt,
                'user_prompt_template': entry.user_prompt_template,
                'variables': entry.variables,
                'note': entry.note,
                'created_at': entry.created_at.isoformat()
            }
            for entry in history_entries
        ]
    })


@admin_bp.route('/ai-prompts/history/<int:history_id>/restore', methods=['POST'])
def restore_prompt_from_history(history_id):
    history_entry = AIPromptHistory.query.get_or_404(history_id)
    prompt = None
    if history_entry.prompt_id:
        prompt = AIPrompt.query.get(history_entry.prompt_id)

    if prompt:
        _snapshot_prompt(prompt, note='Before restore from history')
        prompt.name = history_entry.name
        prompt.description = history_entry.description
        prompt.system_prompt = history_entry.system_prompt
        prompt.user_prompt_template = history_entry.user_prompt_template
        prompt.variables = history_entry.variables
        prompt.updated_at = datetime.utcnow()
    else:
        prompt = AIPrompt(
            prompt_type=history_entry.prompt_type,
            name=history_entry.name,
            description=history_entry.description,
            system_prompt=history_entry.system_prompt,
            user_prompt_template=history_entry.user_prompt_template,
            variables=history_entry.variables,
            is_default=False,
            is_active=True
        )
        db.session.add(prompt)
        db.session.flush()
        history_entry.prompt_id = prompt.id

    db.session.commit()

    return jsonify({'success': True, 'message': 'Prompt restored from history'})

@admin_bp.route('/ai-prompts/initialize-defaults', methods=['POST'])
def initialize_default_prompts():
    """Initialize default AI prompts"""
    try:
        # Check if any prompts already exist
        if AIPrompt.query.count() > 0:
            return jsonify({'success': False, 'message': 'Prompts already exist. Clear existing prompts first.'})
        
        # Default prompts
        default_prompts = [
            {
                'prompt_type': 'quote_analysis',
                'name': 'Default Quote Analysis',
                'description': 'Analyzes quote requirements and provides recommendations',
                'system_prompt': "You are a technical expert in structured cabling, WiFi, CCTV, and door entry systems. Provide detailed analysis and recommendations for installation projects. Focus on practical solutions and cost-effective recommendations.",
                'user_prompt_template': """Analyze this structured cabling project and provide detailed recommendations:

Project: {project_title}
Description: {project_description}
Building Type: {building_type}
Building Size: {building_size} sqm
Floors: {number_of_floors}
Rooms: {number_of_rooms}
Site Address: {site_address}

Requirements:
- WiFi: {wifi_requirements}
- CCTV: {cctv_requirements}
- Door Entry: {door_entry_requirements}
- Special Requirements: {special_requirements}

Please provide:
1. Detailed technical analysis
2. Recommended products (specific models and quantities)
3. Estimated installation time in hours
4. Alternative solutions with pros/cons
5. Any special considerations or challenges

Format your response as JSON with these keys:
- analysis: detailed text analysis
- products: array of recommended products with quantities
- estimated_time: hours
- alternatives: array of alternative solutions""",
                'is_default': True,
                'is_active': True
            },
            {
                'prompt_type': 'product_search',
                'name': 'Default Product Search',
                'description': 'Searches for products based on category and query',
                'system_prompt': "You are a product expert for structured cabling, networking, and security equipment. Provide accurate product recommendations with specific models and realistic pricing.",
                'user_prompt_template': "Search for {category} products related to: {query}\n\nProvide a list of specific products with:\n- Product name and model\n- Brief description\n- Typical use case\n- Estimated price range\n\nFormat as JSON array of objects.",
                'is_default': True,
                'is_active': True
            },
            {
                'prompt_type': 'building_analysis',
                'name': 'Default Building Analysis',
                'description': 'Analyzes building information for cabling projects',
                'system_prompt': "You are a building analysis expert specializing in structured cabling installations. Analyze building information and provide technical insights for cabling projects.",
                'user_prompt_template': "Analyze this building for structured cabling requirements:\n\nAddress: {address}\nBuilding Type: {building_type}\nSize: {building_size} sqm\n\nProvide recommendations for:\n- Cable routing strategies\n- Equipment placement locations\n- Power requirements\n- Access considerations\n- Potential challenges",
                'is_default': True,
                'is_active': True
            }
        ]
        
        # Add default prompts
        for prompt_data in default_prompts:
            prompt = AIPrompt(**prompt_data)
            db.session.add(prompt)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Initialized {len(default_prompts)} default prompts'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api-settings')
def api_settings():
    """Manage API settings"""
    api_settings = APISettings.query.all()
    day_rate_setting = AdminSetting.query.filter_by(key='day_rate').first()
    cost_per_mile_setting = AdminSetting.query.filter_by(key='cost_per_mile').first()
    office_name_setting = AdminSetting.query.filter_by(key='company_name').first()
    office_address_setting = AdminSetting.query.filter_by(key='office_address').first()
    office_postcode_setting = AdminSetting.query.filter_by(key='office_postcode').first()
    
    openai_key = ''
    google_maps_key = ''
    companies_house_key = ''
    openai_status = False
    google_maps_status = False
    companies_house_status = False
    
    for setting in api_settings:
        if setting.service_name == 'openai':
            openai_key = setting.api_key[:8] + '...' if setting.api_key else ''
            openai_status = bool(setting.api_key and setting.is_active)
        elif setting.service_name == 'google_maps':
            google_maps_key = setting.api_key[:8] + '...' if setting.api_key else ''
            google_maps_status = bool(setting.api_key and setting.is_active)
        elif setting.service_name == 'companies_house':
            companies_house_key = setting.api_key[:8] + '...' if setting.api_key else ''
            companies_house_status = bool(setting.api_key and setting.is_active)
    
    day_rate_value = day_rate_setting.value if day_rate_setting else ''
    cost_per_mile_value = cost_per_mile_setting.value if cost_per_mile_setting else ''
    office_settings = {
        'company_name': office_name_setting.value if office_name_setting else '',
        'office_address': office_address_setting.value if office_address_setting else '',
        'office_postcode': office_postcode_setting.value if office_postcode_setting else ''
    }

    return render_template(
        'admin/api_settings.html',
        api_settings=api_settings,
        openai_key=openai_key,
        google_maps_key=google_maps_key,
        companies_house_key=companies_house_key,
        openai_status=openai_status,
        google_maps_status=google_maps_status,
        companies_house_status=companies_house_status,
        day_rate_value=day_rate_value,
        cost_per_mile_value=cost_per_mile_value,
        office_settings=office_settings
    )

@admin_bp.route('/api-settings/update', methods=['POST'])
def update_api_settings():
    """Update API settings"""
    try:
        data = request.get_json()
        
        service_name = data.get('service_name')
        
        if service_name in ['openai', 'google_maps', 'companies_house']:
            api_key = data.get('api_key')
            api_setting = APISettings.query.filter_by(service_name=service_name).first()
            if api_setting:
                api_setting.api_key = api_key
            else:
                api_setting = APISettings(service_name=service_name, api_key=api_key)
                db.session.add(api_setting)
            db.session.commit()
            from utils.ai_helper import AIHelper
            AIHelper().refresh_clients()
            return jsonify({'success': True, 'message': 'API settings updated successfully'})
        elif service_name == 'day_rate':
            rate_value = str(data.get('rate', '0')).strip()
            setting = AdminSetting.query.filter_by(key='day_rate').first()
            if setting:
                setting.value = rate_value
            else:
                db.session.add(AdminSetting(key='day_rate', value=rate_value))
            db.session.commit()
            return jsonify({'success': True, 'message': 'Day rate updated successfully'})
        elif service_name == 'cost_per_mile':
            rate_value = str(data.get('rate', '0')).strip()
            setting = AdminSetting.query.filter_by(key='cost_per_mile').first()
            if setting:
                setting.value = rate_value
            else:
                db.session.add(AdminSetting(key='cost_per_mile', value=rate_value))
            db.session.commit()
            return jsonify({'success': True, 'message': 'Cost per mile updated successfully'})
        elif service_name == 'office_settings':
            company_name = data.get('company_name', '').strip()
            office_address = data.get('office_address', '').strip()
            office_postcode = data.get('office_postcode', '').strip()

            for key, value in (
                ('company_name', company_name),
                ('office_address', office_address),
                ('office_postcode', office_postcode)
            ):
                setting = AdminSetting.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    db.session.add(AdminSetting(key=key, value=value))
            db.session.commit()
            return jsonify({'success': True, 'message': 'Office details updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Invalid service name'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/calculate-travel-distance', methods=['POST'])
def calculate_travel_distance():
    try:
        data = request.get_json() or {}
        sample_address = data.get('sample_address') or '10 Downing Street, London'

        office_address = AdminSetting.query.filter_by(key='office_address').first()
        if not office_address or not office_address.value:
            return jsonify({'success': False, 'message': 'Office address not configured.'})

        from utils.ai_helper import AIHelper
        ai_helper = AIHelper()
        if not ai_helper.gmaps_client:
            return jsonify({'success': False, 'message': 'Google Maps key not configured.'})

        office_geocode = ai_helper.gmaps_client.geocode(office_address.value)
        job_geocode = ai_helper.gmaps_client.geocode(sample_address)
        if not office_geocode or not job_geocode:
            return jsonify({'success': False, 'message': 'Unable to geocode one of the addresses.'})

        office_location = office_geocode[0]['geometry']['location']
        job_location = job_geocode[0]['geometry']['location']

        from math import radians, sin, cos, sqrt, atan2
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        distance_km = haversine(
            office_location['lat'], office_location['lng'],
            job_location['lat'], job_location['lng']
        )
        estimated_minutes = (distance_km / 50.0) * 60.0

        return jsonify({
            'success': True,
            'message': f'Approx. {distance_km:.1f} km, {estimated_minutes:.0f} minutes travel from office to sample site.'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/users')
def manage_users():
    """Manage users"""
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['POST'])
def add_user():
    """Add new user"""
    try:
        data = request.get_json()
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            is_admin=bool(data.get('is_admin', False))
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User added successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/quotes')
def manage_quotes():
    """Manage all quotes"""
    page = request.args.get('page', 1, type=int)
    quotes = Quote.query.order_by(Quote.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template('admin/quotes.html', quotes=quotes)

@admin_bp.route('/quotes/<int:quote_id>/delete', methods=['POST'])
def delete_quote(quote_id):
    """Delete a quote"""
    try:
        quote = Quote.query.get_or_404(quote_id)
        db.session.delete(quote)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Quote deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/suppliers')
def manage_suppliers():
    """Manage suppliers and categories"""
    categories = Category.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    
    # Group suppliers by category
    suppliers_by_category = {}
    for supplier in suppliers:
        if supplier.category_id not in suppliers_by_category:
            suppliers_by_category[supplier.category_id] = []
        suppliers_by_category[supplier.category_id].append(supplier)
    
    return render_template('admin/suppliers.html', 
                         categories=categories, 
                         suppliers_by_category=suppliers_by_category)

@admin_bp.route('/suppliers/categories', methods=['POST'])
def create_category():
    """Create a new category"""
    try:
        data = request.get_json()
        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            is_active=True
        )
        db.session.add(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Category created successfully', 'category_id': category.id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/suppliers/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update a category"""
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        category.name = data['name']
        category.description = data.get('description', '')
        category.is_active = data.get('is_active', True)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Category updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/suppliers/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    try:
        category = Category.query.get_or_404(category_id)
        category.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Category deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    """Create a new supplier"""
    try:
        data = request.get_json()
        supplier = Supplier(
            name=data['name'],
            website=data.get('website', ''),
            pricing_url=data.get('pricing_url', ''),
            category_id=data['category_id'],
            is_preferred=data.get('is_preferred', False),
            notes=data.get('notes', '')
        )
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Supplier created successfully', 'supplier_id': supplier.id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update a supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()
        
        supplier.name = data['name']
        supplier.website = data.get('website', '')
        supplier.pricing_url = data.get('pricing_url', '')
        supplier.category_id = data['category_id']
        supplier.is_preferred = data.get('is_preferred', False)
        supplier.notes = data.get('notes', '')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Supplier updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """Delete a supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        supplier.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Supplier deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/pricing')
def manage_pricing_data():
    """Manage pricing data and refresh from suppliers"""
    pricing_service = PricingService()
    pricing_summary = pricing_service.get_supplier_pricing_summary()
    
    return render_template('admin/pricing_data.html', pricing_summary=pricing_summary)

@admin_bp.route('/pricing/refresh', methods=['POST'])
def refresh_pricing():
    """Refresh all pricing from supplier websites"""
    try:
        pricing_service = PricingService()
        result = pricing_service.refresh_all_pricing()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to refresh pricing')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/pricing/test/<supplier_name>/<product_name>')
def test_pricing(supplier_name, product_name):
    """Test pricing lookup for a specific supplier and product"""
    try:
        pricing_service = PricingService()
        result = pricing_service.get_product_price(supplier_name, product_name, force_refresh=True)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500