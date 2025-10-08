from typing import Any, Dict, List, Optional

from openai import OpenAI
import pandas as pd
import json
import os
import re

from models import APISettings

class AIPricingExtractor:
    def __init__(self):
        self.openai_client: Optional[Any] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client from database settings"""
        try:
            openai_setting = APISettings.query.filter_by(service_name='openai').first()
            if openai_setting and openai_setting.api_key:
                self.openai_client = OpenAI(
                    api_key=openai_setting.api_key,
                    timeout=30.0
                )
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
    
    def extract_pricing_from_spreadsheet(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract pricing data from any spreadsheet format using AI"""
        try:
            # Read the spreadsheet
            df = self._read_spreadsheet(file_path)
            
            if df is None or df.empty:
                return []
            
            # Convert to text for AI analysis
            spreadsheet_text = self._dataframe_to_text(df)
            
            # Use AI to extract pricing information
            pricing_data = self._ai_extract_pricing(spreadsheet_text)
            
            return pricing_data
            
        except Exception as e:
            print(f"Error extracting pricing from spreadsheet: {e}")
            return []
    
    def _read_spreadsheet(self, file_path: str):
        """Read spreadsheet in any format"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.csv':
                return pd.read_csv(file_path, encoding='utf-8')
            elif file_extension in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            elif file_extension == '.ods':
                return pd.read_excel(file_path, engine='odf')
            else:
                # Try to read as CSV first, then Excel
                try:
                    return pd.read_csv(file_path, encoding='utf-8')
                except:
                    return pd.read_excel(file_path)
                    
        except Exception as e:
            print(f"Error reading spreadsheet: {e}")
            return None
    
    def _dataframe_to_text(self, df) -> str:
        """Convert dataframe to readable text for AI analysis"""
        try:
            if df is None or df.empty:
                return ""
            
            # Take first 100 rows to avoid token limits
            sample_df = df.head(100)
            
            # Convert to text representation
            text_representation = f"Spreadsheet Data:\n\n"
            text_representation += f"Columns: {list(sample_df.columns)}\n\n"
            text_representation += sample_df.to_string(index=False)
            
            return text_representation
            
        except Exception as e:
            print(f"Error converting dataframe to text: {e}")
            return ""
    
    def _ai_extract_pricing(self, spreadsheet_text: str) -> List[Dict[str, Any]]:
        """Use AI to extract pricing information from spreadsheet text"""
        if not self.openai_client:
            return []
        
        try:
            prompt = f"""
            Analyze this spreadsheet data and extract pricing information for structured cabling, networking, and security equipment.
            
            For each pricing item found, extract:
            - Product name/model
            - Category (cabling, wifi, cctv, door_entry, labor, other)
            - Subcategory (optional)
            - Unit (meter, piece, hour, etc.)
            - Price/cost
            - Supplier (if mentioned)
            - Part number (if available)
            - Description (if available)
            
            Focus on:
            - Cables (Cat5e, Cat6, Cat6a, Fiber)
            - Network equipment (switches, routers, access points)
            - Security equipment (cameras, door systems)
            - Labor rates
            - Installation materials
            
            Return the data as a JSON array of objects with these exact field names:
            - product_name
            - category
            - subcategory
            - unit
            - cost_per_unit
            - supplier
            - part_number
            - description
            
            If a field is not available, use null.
            Only return valid JSON, no other text.
            
            Spreadsheet data:
            {spreadsheet_text}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting pricing data from spreadsheets. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                # temperature=0.3,  # GPT-5 only supports default temperature
                max_completion_tokens=20000
            )
            
            result_text = response.choices[0].message.content
            
            # Clean and parse JSON
            json_text = self._extract_json_from_response(result_text)
            pricing_data = json.loads(json_text)
            
            # Validate and clean data
            validated_data = self._validate_pricing_data(pricing_data)
            
            return validated_data
            
        except Exception as e:
            print(f"Error in AI pricing extraction: {e}")
            return []
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from AI response"""
        try:
            # Look for JSON array
            if '[' in response_text and ']' in response_text:
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                return response_text[start:end]
            
            # Look for JSON object
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_obj = response_text[start:end]
                # Wrap single object in array
                return f"[{json_obj}]"
            
            return "[]"
            
        except Exception as e:
            print(f"Error extracting JSON: {e}")
            return "[]"
    
    def _validate_pricing_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Validate and clean pricing data"""
        validated = []
        
        for item in data:
            try:
                # Ensure required fields exist
                validated_item = {
                    'product_name': str(item.get('product_name', '')).strip() if item.get('product_name') else None,
                    'category': str(item.get('category', '')).lower().strip() if item.get('category') else 'other',
                    'subcategory': str(item.get('subcategory', '')).strip() if item.get('subcategory') else None,
                    'unit': str(item.get('unit', 'piece')).lower().strip() if item.get('unit') else 'piece',
                    'cost_per_unit': float(item.get('cost_per_unit', 0)) if item.get('cost_per_unit') else 0,
                    'supplier': str(item.get('supplier', '')).strip() if item.get('supplier') else None,
                    'part_number': str(item.get('part_number', '')).strip() if item.get('part_number') else None,
                    'description': str(item.get('description', '')).strip() if item.get('description') else None
                }
                
                # Skip if no product name or invalid price
                if not validated_item['product_name'] or validated_item['cost_per_unit'] <= 0:
                    continue
                
                # Validate category
                valid_categories = ['cabling', 'wifi', 'cctv', 'door_entry', 'labor', 'other']
                if validated_item['category'] not in valid_categories:
                    validated_item['category'] = 'other'
                
                # Clean product name
                validated_item['product_name'] = self._clean_product_name(validated_item['product_name'])
                
                validated.append(validated_item)
                
            except Exception as e:
                print(f"Error validating item: {e}")
                continue
        
        return validated
    
    def _clean_product_name(self, product_name: str) -> str:
        """Clean and standardize product names"""
        try:
            # Remove extra whitespace
            cleaned = re.sub(r'\s+', ' ', product_name.strip())
            
            # Common standardizations
            cleaned = cleaned.replace('CAT 5E', 'Cat5e')
            cleaned = cleaned.replace('CAT 6', 'Cat6')
            cleaned = cleaned.replace('CAT 6A', 'Cat6a')
            cleaned = cleaned.replace('CAT6A', 'Cat6a')
            cleaned = cleaned.replace('CAT5E', 'Cat5e')
            cleaned = cleaned.replace('CAT6', 'Cat6')
            
            return cleaned
            
        except Exception as e:
            print(f"Error cleaning product name: {e}")
            return product_name
    
    def get_web_pricing(self, product_name: str, category: str = None) -> Dict[str, Any]:
        """Get current pricing from web sources using AI"""
        if not self.openai_client:
            return None
        
        try:
            prompt = f"""
            Search for current pricing information for this product: "{product_name}"
            
            Category: {category or 'general'}
            
            Please provide:
            - Current market price
            - Typical price range
            - Supplier information
            - Product specifications (if relevant)
            
            Focus on:
            - UK/EU pricing in GBP/EUR
            - Major suppliers and distributors
            - Current availability
            - Any special offers or bulk pricing
            
            Return as JSON with these fields:
            - estimated_price
            - price_range_min
            - price_range_max
            - currency
            - suppliers
            - notes
            
            If you cannot find specific pricing, return null values.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert at finding current pricing for technical products. Provide accurate, recent pricing information."},
                    {"role": "user", "content": prompt}
                ],
                # temperature=0.3,  # GPT-5 only supports default temperature
                max_completion_tokens=10000
            )
            
            result_text = response.choices[0].message.content
            json_text = self._extract_json_from_response(result_text)
            
            if json_text != "[]":
                pricing_info = json.loads(json_text)
                if isinstance(pricing_info, list) and len(pricing_info) > 0:
                    return pricing_info[0]
                elif isinstance(pricing_info, dict):
                    return pricing_info
            
            return None
            
        except Exception as e:
            print(f"Error getting web pricing: {e}")
            return None
    
    def analyze_pricing_gaps(self, missing_products: List[str]) -> List[Dict[str, Any]]:
        """Analyze products that need pricing and suggest web searches"""
        if not self.openai_client:
            return []
        
        try:
            prompt = f"""
            These products are missing from our pricing database:
            {', '.join(missing_products)}
            
            For each product, suggest:
            - Where to find pricing (supplier websites, distributors)
            - Alternative product names to search for
            - Estimated price ranges
            - Category classification
            
            Return as JSON array with fields:
            - product_name
            - suggested_suppliers
            - alternative_names
            - estimated_price_range
            - category
            - search_tips
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert at finding pricing for technical products and suggesting search strategies."},
                    {"role": "user", "content": prompt}
                ],
                # temperature=0.5,  # GPT-5 only supports default temperature
                max_completion_tokens=15000
            )
            
            result_text = response.choices[0].message.content
            json_text = self._extract_json_from_response(result_text)
            
            return json.loads(json_text) if json_text != "[]" else []
            
        except Exception as e:
            print(f"Error analyzing pricing gaps: {e}")
            return []
