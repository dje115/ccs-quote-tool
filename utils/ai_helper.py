import json
from typing import Any, Dict, Optional

import googlemaps
from openai import OpenAI

from models import APISettings, AIPrompt, AdminSetting
from utils.pricing_service import PricingService

class AIHelper:
    def __init__(self):
        self.openai_client: Optional[Any] = None
        self.gmaps_client: Optional[googlemaps.Client] = None
        self.pricing_service = PricingService()
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients from database settings"""
        try:
            # Reset clients before attempting initialization so we do not
            # accidentally keep stale instances around when settings change.
            self.openai_client = None
            self.gmaps_client = None

            # Initialize OpenAI
            openai_setting = APISettings.query.filter_by(service_name='openai').first()
            print(f"OpenAI setting found: {openai_setting is not None}")
            if openai_setting:
                print(f"OpenAI API key exists: {bool(openai_setting.api_key)}")
                print(f"OpenAI API key length: {len(openai_setting.api_key) if openai_setting.api_key else 0}")
            
            if openai_setting and openai_setting.api_key:
                # openai>=1.2 exposes the OpenAI client class for direct usage.
                self.openai_client = OpenAI(
                    api_key=openai_setting.api_key,
                    timeout=300.0  # 5 minutes timeout for GPT-5
                )
                print("OpenAI client initialized successfully")
            else:
                print("OpenAI client not initialized - no API key")
            
            # Initialize Google Maps
            gmaps_setting = APISettings.query.filter_by(service_name='google_maps').first()
            if gmaps_setting and gmaps_setting.api_key:
                self.gmaps_client = googlemaps.Client(key=gmaps_setting.api_key)
                print("Google Maps client initialized successfully")
                
        except Exception as e:
            print(f"Error initializing API clients: {e}")
    
    def refresh_clients(self):
        """Refresh API clients after settings update"""
        self._initialize_clients()
    
    def get_prompt(self, prompt_type, is_default=True):
        """Get AI prompt from database"""
        try:
            query = AIPrompt.query.filter_by(prompt_type=prompt_type, is_active=True)
            if is_default:
                query = query.filter_by(is_default=True)
            
            prompt = query.first()
            if prompt:
                return {
                    'system_prompt': prompt.system_prompt,
                    'user_prompt_template': prompt.user_prompt_template,
                    'variables': json.loads(prompt.variables) if prompt.variables else []
                }
            else:
                # Return default prompts if none found in database
                return self._get_default_prompt(prompt_type)
        except Exception as e:
            print(f"Error getting prompt: {e}")
            return self._get_default_prompt(prompt_type)
    
    def _get_default_prompt(self, prompt_type):
        """Get default prompts if none exist in database"""
        default_prompts = {
            'quote_analysis': {
                'system_prompt': (
                    "You are a seasoned structured cabling contractor and estimator."
                    " You produce practical, buildable quotations, highlight assumptions,"
                    " and make sensible allowances for labour and materials."
                ),
                'user_prompt_template': """
You are a structured cabling contractor. The client has supplied the information below.

Project Title: {project_title}
Description: {project_description}
Building Type: {building_type}
Building Size: {building_size} sqm
Number of Floors: {number_of_floors}
Number of Rooms/Areas: {number_of_rooms}
Site Address: {site_address}

Solution Requirements:
- WiFi installation needed: {wifi_requirements}
- CCTV installation needed: {cctv_requirements}
- Door entry installation needed: {door_entry_requirements}
- Special requirements or constraints: {special_requirements}

Your tasks:
1. Identify any missing critical details (containment type, ceiling construction, patch panel counts, testing & certification, rack power, etc.). Ask up to 5 short clarification questions.
2. When sufficient information is available (or you must make reasonable assumptions), prepare a structured cabling quotation that includes: client requirement restatement, scope of works, materials list, labour estimate, and assumptions/exclusions.

Response rules:
- Always respond in JSON format.
- When the caller is only requesting questions (questions_only mode) return: {"clarifications": [..]}.
- Otherwise return a JSON object with these keys:
  - analysis: concise narrative summary (string).
  - products: array of recommended products with EXACT pricing data:
      * item: product name (string)
      * quantity: numeric quantity only (number, not text like "Allowance")
      * unit: unit type (string: "each", "meters", "box", etc.)
      * unit_price: exact unit price in GBP (number)
      * total_price: exact total price in GBP (number)
      * part_number: manufacturer part number (string)
      * notes: installation notes (string)
  - alternatives: array describing optional approaches with pros/cons.
  - estimated_time: total installation hours (number).
  - labour_breakdown: array of objects describing tasks with hours, engineer_count, day_rate, cost, notes.
  - clarifications: array of outstanding clarification questions (if any remain).
  - quotation: object containing:
      * client_requirement (string summary)
      * scope_of_works (array of bullet strings)
      * materials (array of objects with item, quantity, unit_price, total_price, part_number, notes)
      * labour (object with engineers, hours, day_rate, total_cost, notes)
      * assumptions_exclusions (array of strings)

CRITICAL PRICING REQUIREMENTS:
- All quantities MUST be numeric values only (e.g., 52.0, not "52.0 each" or "Allowance")
- All prices MUST be real GBP amounts (e.g., 125.00 for U6-Pro, 89.00 for U6-Lite)
- Include part numbers for all products when available
- Use real pricing from supplier websites when possible
- If you cannot find real pricing, use realistic estimates but note that these will be marked as estimated (*)
- Always provide unit_price and total_price as numbers, never as text

If details are missing, state the assumption you are making inside the quotation sections and keep questions short and specific.
""",
                'variables': ['project_title', 'project_description', 'building_type', 'building_size', 'number_of_floors', 'number_of_rooms', 'site_address', 'wifi_requirements', 'cctv_requirements', 'door_entry_requirements', 'special_requirements']
            },
            'product_search': {
                'system_prompt': "You are a product expert for structured cabling, networking, and security equipment. Provide accurate product recommendations.",
                'user_prompt_template': "Search for {category} products related to: {query}\n\nProvide a list of specific products with:\n- Product name and model\n- Brief description\n- Typical use case\n- Estimated price range\n\nFormat as JSON array of objects.",
                'variables': ['category', 'query']
            },
            'building_analysis': {
                'system_prompt': "You are a building analysis expert. Analyze building information and provide technical insights for cabling projects.",
                'user_prompt_template': "Analyze this building for structured cabling requirements:\n\nAddress: {address}\nBuilding Type: {building_type}\nSize: {building_size} sqm\n\nProvide recommendations for:\n- Cable routing\n- Equipment placement\n- Power requirements\n- Access considerations",
                'variables': ['address', 'building_type', 'building_size']
            }
        }
        
        return default_prompts.get(prompt_type, {
            'system_prompt': "You are a helpful assistant.",
            'user_prompt_template': "{query}",
            'variables': ['query']
        })
    
    def analyze_quote_requirements(self, quote, clarification_answers=None, questions_only=False):
        """Analyze quote requirements and provide recommendations"""
        if not self.openai_client:
            return None
        
        try:
            prompt_config = self.get_prompt('quote_analysis')
            # Get brand preferences
            brand_settings = AdminSetting.query.filter(AdminSetting.key.like('%_brands')).all()
            brand_info = ""
            if brand_settings:
                brand_info = "\n\n**Brand Preferences:**\n"
                for setting in brand_settings:
                    category = setting.key.replace('_brands', '').replace('_', ' ').title()
                    brands = setting.value
                    brand_info += f"- {category}: {brands}\n"
            
            # Get preferred suppliers information
            from models import Category, Supplier
            suppliers_info = ""
            categories = Category.query.filter_by(is_active=True).all()
            for category in categories:
                preferred_suppliers = Supplier.query.filter_by(
                    category_id=category.id, 
                    is_preferred=True, 
                    is_active=True
                ).all()
                if preferred_suppliers:
                    suppliers_info += f"\n**{category.name} Suppliers:**\n"
                    for supplier in preferred_suppliers:
                        suppliers_info += f"- {supplier.name}"
                        if supplier.website:
                            suppliers_info += f" ({supplier.website})"
                        if supplier.notes:
                            suppliers_info += f" - {supplier.notes}"
                        suppliers_info += "\n"
            
            if suppliers_info:
                suppliers_info = f"\n\n**Preferred Suppliers for Pricing Reference:**{suppliers_info}"
                suppliers_info += "\nWhen recommending products, prioritize these suppliers and try to get accurate pricing from their websites when possible."
            
            # Get day rate from settings
            day_rate_setting = AdminSetting.query.filter_by(key='day_rate').first()
            day_rate = day_rate_setting.value if day_rate_setting else '300'
            day_rate_info = f"\n\n**Labour Rate:** £{day_rate} per pair of engineers per day (8-hour day)\n**CRITICAL: £{day_rate} is the TOTAL cost for BOTH engineers working together for one day**"
            
            # Use string replacement instead of format to avoid issues with JSON braces
            user_prompt = prompt_config['user_prompt_template']
            replacements = {
                '{project_title}': quote.project_title or '',
                '{project_description}': quote.project_description or '',
                '{building_type}': quote.building_type or '',
                '{building_size}': str(quote.building_size or 0),
                '{number_of_floors}': str(quote.number_of_floors or 1),
                '{number_of_rooms}': str(quote.number_of_rooms or 1),
                '{site_address}': quote.site_address or '',
                '{wifi_requirements}': str(quote.wifi_requirements),
                '{cctv_requirements}': str(quote.cctv_requirements),
                '{door_entry_requirements}': str(quote.door_entry_requirements),
                '{special_requirements}': quote.special_requirements or ''
            }
            for placeholder, value in replacements.items():
                user_prompt = user_prompt.replace(placeholder, value)
            # Get real pricing data for common products
            real_pricing_info = self._get_real_pricing_data()
            
            # Add real pricing reference to the prompt
            if real_pricing_info:
                user_prompt += f"\n\n**REAL PRICING REFERENCE (Use these exact prices):**\n{real_pricing_info}"
                user_prompt += "\n\n**CRITICAL:** Use the exact pricing above. Do not estimate or guess prices. All unit_price and total_price values must be real numbers, not text."
            
            # Add consistency context from historical data
            try:
                from utils.quote_consistency import QuoteConsistencyManager
                consistency_manager = QuoteConsistencyManager()
                consistency_context = consistency_manager.get_consistency_context_for_ai(quote)
                if consistency_context:
                    user_prompt += f"\n\n{consistency_context}"
            except Exception as e:
                print(f"Error adding consistency context: {e}")
            
            user_prompt = user_prompt + brand_info + day_rate_info + suppliers_info

            if clarification_answers:
                lines = []
                for idx, item in enumerate(clarification_answers, start=1):
                    question = item.get('question') or ''
                    answer = item.get('answer') or ''
                    lines.append(f"{idx}. Question: {question}\n   Answer: {answer if answer else 'Not provided'}")
                if lines:
                    user_prompt += "\n\nClarification Responses:\n" + "\n".join(lines)

            if questions_only:
                guide_prompt = (
                    "Return a JSON object with a single key 'clarifications'."
                    " The value must be an array (even if empty) of short questions you still need answered."
                )
            else:
                guide_prompt = (
                    "Return a JSON object with these keys: analysis, products, labour_breakdown, clarifications, quotation."
                    " Keep the JSON structure simple. For quotation, use simple objects without deep nesting."
                )

            response = self.openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": guide_prompt},
                {"role": "system", "content": prompt_config['system_prompt']},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=50000,  # GPT-5 can handle up to 400k tokens
            timeout=300  # 5 minutes for larger GPT-5 responses
        )
 
            message_content = response.choices[0].message.content
            print(f"DEBUG: AI response received, length: {len(message_content) if message_content else 0}")
            # Debug logging to inspect raw responses when unexpected shapes appear
            if not message_content:
                print("AI response message_content was empty or None")
            if questions_only:
                clarifications = []
                try:
                    parsed = json.loads(message_content)
                    if isinstance(parsed, dict):
                        clarifications = parsed.get('clarifications') or []
                        if not isinstance(clarifications, list):
                            clarifications = []
                except Exception:
                    pass
                return {'clarifications': clarifications}

            try:
                result = self._parse_analysis_response(message_content, quote)
                # Add the raw response to the result for database storage
                if result and isinstance(result, dict):
                    result['ai_raw_response'] = message_content
                return result
            except Exception as parse_error:
                print(f"Parse failure. Error: {parse_error}")
                print("Raw message content:", repr(message_content))
                print("Message content type:", type(message_content))
                # Try to return a fallback response instead of re-parsing
                return {
                    'analysis': str(message_content) if message_content else 'AI analysis failed',
                    'products': [],
                    'estimated_time': self._estimate_time_basic(quote),
                    'alternatives': [],
                    'clarifications': [],
                    'labour_breakdown': [],
                    'quotation': {
                        'client_requirement': '',
                        'scope_of_works': [],
                        'materials': [],
                        'labour': {},
                        'assumptions_exclusions': []
                    },
                    'ai_raw_response': message_content  # Save raw response even in fallback
                }
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_analysis_response(self, response_text, quote):
        """Parse AI response and extract structured data"""
        try:
            if isinstance(response_text, dict):
                data = response_text
            elif isinstance(response_text, str):
                stripped = response_text.strip()
                if stripped.startswith('{') and stripped.count('{') == stripped.count('}'):
                    data = json.loads(stripped)
                else:
                    import re
                    match = re.search(r'\{(.|\n)*\}', stripped)
                    if match:
                        json_text = match.group(0)
                        data = json.loads(json_text)
                    else:
                        data = None
            else:
                data = None

            if isinstance(data, dict):
                if 'estimated_time' not in data and 'estimated_hours' in data:
                    data['estimated_time'] = data.get('estimated_hours')
                data.setdefault('clarifications', [])
                data.setdefault('labour_breakdown', [])
                data.setdefault('quotation', {})
                data.setdefault('travel_distance_miles', 0)
                data.setdefault('travel_time_minutes', 0)
                if not data.get('estimated_time'):
                    data['estimated_time'] = self._estimate_time_basic(quote)
                if isinstance(data['quotation'], dict):
                    data['quotation'].setdefault('client_requirement', '')
                    data['quotation'].setdefault('scope_of_works', [])
                    data['quotation'].setdefault('materials', [])
                    data['quotation'].setdefault('labour', {})
                    data['quotation'].setdefault('assumptions_exclusions', [])
                return data

            return {
                'analysis': response_text,
                'products': [],
                'estimated_time': self._estimate_time_basic(quote),
                'alternatives': [],
                'clarifications': [],
                'labour_breakdown': [],
                'quotation': {
                    'client_requirement': '',
                    'scope_of_works': [],
                    'materials': [],
                    'labour': {},
                    'assumptions_exclusions': []
                },
                'travel_distance_miles': 0,
                'travel_time_minutes': 0,
                'ai_raw_response': response_text
            }
        except Exception as e:
            print(f"Error parsing analysis response: {e}")
            return {
                'analysis': response_text,
                'products': [],
                'estimated_time': self._estimate_time_basic(quote),
                'alternatives': [],
                'clarifications': [],
                'labour_breakdown': [],
                'quotation': {
                    'client_requirement': '',
                    'scope_of_works': [],
                    'materials': [],
                    'labour': {},
                    'assumptions_exclusions': []
                },
                'travel_distance_miles': 0,
                'travel_time_minutes': 0,
                'ai_raw_response': response_text
            }
    
    def estimate_hours_from_ai(self, analysis_data, fallback_quote):
        """Pick the best effort estimate from AI data with fallback"""
        if not analysis_data:
            return self._estimate_time_basic(fallback_quote)
        if isinstance(analysis_data, dict):
            if analysis_data.get('estimated_time'):
                try:
                    return float(analysis_data['estimated_time'])
                except (ValueError, TypeError):
                    pass
            if analysis_data.get('estimated_hours'):
                try:
                    return float(analysis_data['estimated_hours'])
                except (ValueError, TypeError):
                    pass
        return self._estimate_time_basic(fallback_quote)
    
    def _estimate_time_basic(self, quote):
        """Basic time estimation without AI"""
        base_hours = 8  # Base installation time
        
        if quote.wifi_requirements:
            base_hours += 4
        if quote.cctv_requirements:
            base_hours += 6
        if quote.door_entry_requirements:
            base_hours += 3
        
        # Scale by building size
        if quote.building_size:
            size_factor = min(quote.building_size / 100, 3)  # Max 3x multiplier
            base_hours = int(base_hours * (1 + size_factor))
        
        return base_hours
    
    def search_products(self, query, category=None):
        """Search for products using AI"""
        if not self.openai_client:
            return []
        
        try:
            # Get prompt from database
            prompt_config = self.get_prompt('product_search')
            
            # Format user prompt
            user_prompt = prompt_config['user_prompt_template'].format(
                category=category or 'general',
                query=query
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": prompt_config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=10000
            )
            
            response_text = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                if '[' in response_text and ']' in response_text:
                    json_start = response_text.find('[')
                    json_end = response_text.rfind(']') + 1
                    json_text = response_text[json_start:json_end]
                    return json.loads(json_text)
            except:
                pass
            
            return []
            
        except Exception as e:
            print(f"Error in product search: {e}")
            return []
    
    def get_building_info(self, address):
        """Get building information using Google Maps API"""
        if not self.gmaps_client:
            return None
        
        try:
            # Geocode the address
            geocode_result = self.gmaps_client.geocode(address)
            
            if not geocode_result:
                return None
            
            place_id = geocode_result[0]['place_id']
            
            # Get detailed place information
            place_details = self.gmaps_client.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'geometry', 'types', 'url']
            )
            
            place_info = place_details['result']
            
            # Calculate approximate building size based on location type
            building_size = self._estimate_building_size(place_info)
            
            return {
                'name': place_info.get('name', ''),
                'formatted_address': place_info.get('formatted_address', address),
                'types': place_info.get('types', []),
                'estimated_size': building_size,
                'google_url': place_info.get('url', ''),
                'coordinates': place_info['geometry']['location']
            }
            
        except Exception as e:
            print(f"Error getting building info: {e}")
            return None
    
    def calculate_travel_details(self, origin_address, destination_address):
        if not self.gmaps_client:
            return None

        try:
            directions = self.gmaps_client.directions(
                origin_address,
                destination_address,
                mode='driving'
            )
            if not directions:
                return None

            leg = directions[0]['legs'][0]
            distance_km = leg['distance']['value'] / 1000.0
            duration_minutes = leg['duration']['value'] / 60.0
            
            # Calculate travel cost based on distance and cost per mile setting
            travel_cost = 0
            try:
                cost_per_mile_setting = AdminSetting.query.filter_by(key='cost_per_mile').first()
                if cost_per_mile_setting and cost_per_mile_setting.value:
                    cost_per_mile = float(cost_per_mile_setting.value)
                    distance_miles = distance_km * 0.621371  # Convert km to miles
                    travel_cost = distance_miles * cost_per_mile
            except Exception as cost_error:
                print(f"Error calculating travel cost: {cost_error}")
            
            # Convert km to miles for UK display
            distance_miles = distance_km * 0.621371
            
            return {
                'origin': leg.get('start_address'),
                'destination': leg.get('end_address'),
                'distance_km': distance_km,
                'distance_miles': distance_miles,
                'duration_minutes': duration_minutes,
                'travel_cost': travel_cost
            }
        except Exception as e:
            print(f"Error calculating travel details: {e}")
            return None

    def _estimate_building_size(self, place_info):
        """Estimate building size based on place type"""
        types = place_info.get('types', [])
        
        # Default size estimates based on building type
        size_estimates = {
            'residential': 150,  # Average house
            'commercial': 500,   # Small office
            'retail': 300,       # Small shop
            'industrial': 1000,  # Warehouse
            'educational': 800,  # School building
            'health': 600,       # Medical building
        }
        
        for place_type in types:
            if place_type in size_estimates:
                return size_estimates[place_type]
        
        # Default for unknown types
        return 200
    
    def get_web_pricing(self, product_name, category=None):
        """Get current pricing from web sources"""
        try:
            # This would integrate with various pricing APIs
            # For now, return mock data
            mock_prices = {
                'unifi': {
                    'U6-Pro': 150,
                    'Dream Machine': 300,
                    'Switch 24': 200
                },
                'cabling': {
                    'Cat6 Cable': 0.5,
                    'Cat5e Cable': 0.3,
                    'Fiber Cable': 2.0
                },
                'cctv': {
                    'UniFi Camera': 200,
                    'Doorbell': 150
                }
            }
            
            # Simple keyword matching for demo
            for category_key, products in mock_prices.items():
                if category and category_key in category.lower():
                    for product, price in products.items():
                        if product.lower() in product_name.lower():
                            return price
            
            return None
            
        except Exception as e:
            print(f"Error getting web pricing: {e}")
            return None
    
    def _get_real_pricing_data(self):
        """Get real pricing data for common products to include in AI prompt"""
        try:
            # Common products to get pricing for (using search terms that match the known prices)
            common_products = [
                ('Ubiquiti UniFi', 'U6-Pro'),
                ('Ubiquiti UniFi', 'U7-Pro'),
                ('Ubiquiti UniFi', 'G5-Bullet'),
                ('Ubiquiti UniFi', 'G5-Dome'),
                ('Ubiquiti UniFi', 'Switch-24-PoE'),
                ('Ubiquiti UniFi', 'Switch-24-PoE-500W'),
                ('Ubiquiti UniFi', 'Dream-Machine-Pro'),
                ('Ubiquiti UniFi', 'NVR-Pro'),
                ('Ubiquiti UniFi', 'Cloud-Key-Plus')
            ]
            
            pricing_info = []
            for supplier, product in common_products:
                try:
                    result = self.pricing_service.get_product_price(supplier, product)
                    if result and result.get('success'):
                        price = result.get('price', 0)
                        source = result.get('source', 'unknown')
                        pricing_info.append(f"- {product}: £{price} (from {source})")
                except Exception as e:
                    print(f"Error getting pricing for {product}: {e}")
                    continue
            
            if pricing_info:
                # Limit to most common products to reduce prompt size
                limited_pricing = pricing_info[:5]  # Only show first 5 products
                return f"\n\n**REAL PRICING DATA (Use these exact prices):**\n" + "\n".join(limited_pricing) + f"\n\n**IMPORTANT:** Use these actual prices when available. For products not listed above, provide realistic estimates but note that estimated pricing will be marked with (*) in the final quote."
            
            return None
            
        except Exception as e:
            print(f"Error getting real pricing data: {e}")
            return None
    
    def test_prompt(self, prompt_type, test_data):
        """Test a prompt with sample data"""
        if not self.openai_client:
            return None
        
        try:
            prompt_config = self.get_prompt(prompt_type)
            
            # Format user prompt with test data
            user_prompt = prompt_config['user_prompt_template'].format(**test_data)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": prompt_config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                # temperature=0.7,  # GPT-5 only supports default temperature
                max_completion_tokens=10000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error testing prompt: {e}")
            return f"Error: {str(e)}"