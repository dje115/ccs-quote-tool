from flask import Blueprint, request, jsonify
from flask_login import login_required
from openai import OpenAI
import googlemaps

from models import APISettings

api_simple_bp = Blueprint('api_simple', __name__)

@api_simple_bp.route('/test-openai-simple', methods=['POST'])
@login_required
def test_openai_simple():
    """Test OpenAI API connection - simplified version"""
    try:
        # Get API key from database
        openai_setting = APISettings.query.filter_by(service_name='openai').first()
        
        if not openai_setting or not openai_setting.api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not configured. Please add your API key in the settings.'
            }), 400
        
        # Create client with minimal parameters
        try:
            client = OpenAI(api_key=openai_setting.api_key)
            
            # Test with a simple request
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Connection successful'"}
                ],
                max_completion_tokens=50
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

@api_simple_bp.route('/test-google-maps-simple', methods=['POST'])
@login_required
def test_google_maps_simple():
    """Test Google Maps API connection - simplified version"""
    try:
        # Get API key from database
        gmaps_setting = APISettings.query.filter_by(service_name='google_maps').first()
        
        if not gmaps_setting or not gmaps_setting.api_key:
            return jsonify({
                'success': False,
                'message': 'Google Maps API key not configured. Please add your API key in the settings.'
            }), 400
        
        # Create client with minimal parameters
        try:
            client = googlemaps.Client(key=gmaps_setting.api_key)
            
            # Test with a simple geocoding request
            result = client.geocode("London, UK")
            
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

@api_simple_bp.route('/test-companies-house', methods=['POST'])
@login_required
def test_companies_house():
    """Test Companies House API connection"""
    try:
        from utils.external_data_service import ExternalDataService
        
        external_service = ExternalDataService()
        
        # Test with a well-known company
        test_company = "Microsoft Corporation"
        result = external_service.get_companies_house_data(test_company)
        
        if result['success']:
            if result['data'].get('company_number'):
                return jsonify({
                    'success': True,
                    'message': f'Companies House API connection successful! Found company data.',
                    'test_search': test_company
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Companies House API connected but returned no data for test query.'
                }), 400
                
        else:
            return jsonify({
                'success': False,
                'message': f'Companies House API error: {result.get("error", "Unknown error")}'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing Companies House API: {str(e)}'
        }), 500

@api_simple_bp.route('/debug-api-settings-simple', methods=['GET'])
@login_required
def debug_api_settings_simple():
    """Debug API settings - simplified version"""
    try:
        openai_setting = APISettings.query.filter_by(service_name='openai').first()
        gmaps_setting = APISettings.query.filter_by(service_name='google_maps').first()
        
        return jsonify({
            'success': True,
            'openai_exists': openai_setting is not None,
            'openai_has_key': openai_setting.api_key is not None if openai_setting else False,
            'openai_key_length': len(openai_setting.api_key) if openai_setting and openai_setting.api_key else 0,
            'gmaps_exists': gmaps_setting is not None,
            'gmaps_has_key': gmaps_setting.api_key is not None if gmaps_setting else False,
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
