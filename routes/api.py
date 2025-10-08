from flask import Blueprint, request, jsonify
from flask_login import login_required
from openai import OpenAI

from models import APISettings, Quote, AdminSetting
from utils.ai_helper import AIHelper
from utils.pricing_helper import PricingHelper

api_bp = Blueprint('api', __name__)

@api_bp.route('/get-building-info', methods=['POST'])
@login_required
def get_building_info():
    """Get building information using Google Maps API"""
    try:
        data = request.get_json()
        address = data.get('address')
        
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        ai_helper = AIHelper()
        building_info = ai_helper.get_building_info(address)
        
        return jsonify({
            'success': True,
            'data': building_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/get-pricing', methods=['POST'])
@login_required
def get_pricing():
    """Get current pricing for products"""
    try:
        data = request.get_json()
        products = data.get('products', [])
        
        pricing_helper = PricingHelper()
        pricing_data = pricing_helper.get_product_pricing(products)
        
        return jsonify({
            'success': True,
            'data': pricing_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/search-products', methods=['POST'])
@login_required
def search_products():
    """Search for products using AI"""
    try:
        data = request.get_json()
        query = data.get('query')
        category = data.get('category')
        
        ai_helper = AIHelper()
        products = ai_helper.search_products(query, category)
        
        return jsonify({
            'success': True,
            'data': products
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/analyze-requirements', methods=['POST'])
@login_required
def analyze_requirements():
    """Analyze project requirements using AI"""
    try:
        data = request.get_json()
        
        # Create a temporary quote object for analysis
        quote = Quote()
        quote.project_title = data.get('project_title', '')
        quote.project_description = data.get('project_description', '')
        quote.site_address = data.get('site_address', '')
        quote.building_type = data.get('building_type', '')
        quote.building_size = data.get('building_size', 0)
        quote.number_of_floors = data.get('number_of_floors', 1)
        quote.number_of_rooms = data.get('number_of_rooms', 1)
        quote.cabling_type = data.get('cabling_type', '')
        quote.wifi_requirements = data.get('wifi_requirements', False)
        quote.cctv_requirements = data.get('cctv_requirements', False)
        quote.door_entry_requirements = data.get('door_entry_requirements', False)
        quote.special_requirements = data.get('special_requirements', '')
        
        ai_helper = AIHelper()
        clarification_answers = data.get('clarification_answers')
        questions_only = data.get('questions_only', False)
        suppress_clarifications = data.get('suppress_clarifications', False)
        analysis = ai_helper.analyze_quote_requirements(quote, clarification_answers, questions_only)
        if analysis and not questions_only:
            try:
                office_address = AdminSetting.query.filter_by(key='office_address').first()
                if office_address and office_address.value and ai_helper.gmaps_client:
                    travel = ai_helper.calculate_travel_details(office_address.value, quote.site_address)
                    if travel:
                        analysis['travel_distance_km'] = travel.get('distance_km')
                        analysis['travel_distance_miles'] = travel.get('distance_miles')
                        analysis['travel_time_minutes'] = travel.get('duration_minutes')
                        analysis['travel_cost'] = travel.get('travel_cost')
                        analysis['travel_origin'] = travel.get('origin')
            except Exception as travel_error:
                print(f"Travel calculation error: {travel_error}")
        if analysis and suppress_clarifications and isinstance(analysis, dict):
            analysis['clarifications'] = []
        
        if analysis is None:
            return jsonify({
                'success': False,
                'error': 'AI analysis failed to return results. Please check your API settings and try again.'
            }), 500
        
        return jsonify({
            'success': True,
            'data': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/update-pricing', methods=['POST'])
@login_required
def update_pricing():
    """Update pricing from external sources"""
    try:
        pricing_helper = PricingHelper()
        updated_count = pricing_helper.update_pricing_from_web()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} pricing items'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/test-openai', methods=['POST'])
@login_required
def test_openai():
    """Test OpenAI API connection"""
    try:
        # Check if API key exists in database first
        openai_setting = APISettings.query.filter_by(service_name='openai').first()
        
        if not openai_setting or not openai_setting.api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not configured. Please add your API key in the settings.'
            }), 400
        
        # Test with a simple prompt - direct API call
        try:
            # Create client with explicit parameters to avoid proxy issues
            client = OpenAI(
                api_key=openai_setting.api_key,
                timeout=30.0
            )
            
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Connection successful' if you can read this message."}
                ],
                max_completion_tokens=1000
            )
            
            result = response.choices[0].message.content
            
            return jsonify({
                'success': True,
                'message': f'OpenAI API connection successful! Response: {result}'
            })
            
        except Exception as api_error:
            return jsonify({
                'success': False,
                'message': f'OpenAI API error: {str(api_error)}'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing OpenAI API: {str(e)}'
        }), 500

@api_bp.route('/test-google-maps', methods=['POST'])
@login_required
def test_google_maps():
    """Test Google Maps API connection"""
    try:
        from utils.ai_helper import AIHelper
        ai_helper = AIHelper()
        ai_helper.refresh_clients()  # Ensure fresh client with latest API key
        
        if not ai_helper.gmaps_client:
            return jsonify({
                'success': False,
                'message': 'Google Maps API key not configured. Please add your API key in the settings.'
            }), 400
        
        # Test with a simple geocoding request
        try:
            result = ai_helper.gmaps_client.geocode("London, UK")
            
            if result:
                return jsonify({
                    'success': True,
                    'message': f'Google Maps API connection successful! Found {len(result)} results for test query.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Google Maps API connected but returned no results for test query.'
                }), 400
                
        except Exception as api_error:
            return jsonify({
                'success': False,
                'message': f'Google Maps API error: {str(api_error)}'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing Google Maps API: {str(e)}'
        }), 500

@api_bp.route('/import-spreadsheet-folder', methods=['POST'])
@login_required
def import_spreadsheet_folder():
    """Import pricing from all spreadsheets in the pricing_spreadsheets folder"""
    try:
        pricing_helper = PricingHelper()
        total_imported = pricing_helper.import_from_spreadsheet_folder()
        
        return jsonify({
            'success': True,
            'message': f'Imported {total_imported} pricing items from spreadsheet folder'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error importing from folder: {str(e)}'
        }), 500

@api_bp.route('/find-missing-pricing', methods=['POST'])
@login_required
def find_missing_pricing():
    """Find products that need pricing and suggest web searches"""
    try:
        data = request.get_json()
        quote_requirements = data.get('quote_requirements', {})
        
        pricing_helper = PricingHelper()
        missing_analysis = pricing_helper.find_missing_pricing(quote_requirements)
        
        return jsonify({
            'success': True,
            'missing_products': missing_analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error finding missing pricing: {str(e)}'
        }), 500

@api_bp.route('/get-web-pricing', methods=['POST'])
@login_required
def get_web_pricing():
    """Get current web pricing for a specific product"""
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        category = data.get('category')
        
        if not product_name:
            return jsonify({
                'success': False,
                'message': 'Product name is required'
            }), 400
        
        pricing_helper = PricingHelper()
        web_pricing = pricing_helper.get_web_pricing_for_product(product_name, category)
        
        if web_pricing:
            return jsonify({
                'success': True,
                'pricing': web_pricing
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Could not find pricing for this product'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting web pricing: {str(e)}'
        }), 500

@api_bp.route('/debug-api-settings', methods=['GET'])
@login_required
def debug_api_settings():
    """Debug API settings to see what's in the database"""
    try:
        from models import APISettings
        
        openai_setting = APISettings.query.filter_by(service_name='openai').first()
        gmaps_setting = APISettings.query.filter_by(service_name='google_maps').first()
        
        return jsonify({
            'success': True,
            'openai_exists': openai_setting is not None,
            'openai_has_key': openai_setting.api_key is not None if openai_setting else False,
            'openai_key_length': len(openai_setting.api_key) if openai_setting and openai_setting.api_key else 0,
            'openai_key_preview': openai_setting.api_key[:10] + '...' if openai_setting and openai_setting.api_key else None,
            'gmaps_exists': gmaps_setting is not None,
            'gmaps_has_key': gmaps_setting.api_key is not None if gmaps_setting else False,
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
