#!/usr/bin/env python3
"""
AI-powered lead generation service
"""

import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from models import APISettings, db
from models_lead_generation import LeadGenerationCampaign, Lead, LeadStatus, LeadSource, LeadGenerationStatus
from utils.external_data_service import ExternalDataService
import openai
import re
# Note: Geopy functionality removed for now - can be added later if needed

class LeadGenerationService:
    def __init__(self):
        self.openai_client = None
        self.external_data_service = ExternalDataService()
        # self.geocoder = Nominatim(user_agent="ccs_quote_tool")  # Removed for now
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client from database settings"""
        try:
            openai_setting = APISettings.query.filter_by(service_name='openai').first()
            if openai_setting and openai_setting.api_key:
                # Set very long timeout for web search operations
                # GPT-5 with web search can take 2-5 minutes
                self.openai_client = openai.OpenAI(
                    api_key=openai_setting.api_key,
                    timeout=300.0  # 5 minutes for Responses API with web search
                )
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
    
    def generate_leads(self, campaign: LeadGenerationCampaign) -> Dict[str, Any]:
        """Generate leads using OpenAI web search + AI analysis"""
        if not self.openai_client:
            return {
                'success': False,
                'error': 'OpenAI client not initialized'
            }
        
        try:
            # Update campaign status
            campaign.status = LeadGenerationStatus.RUNNING
            campaign.started_at = datetime.utcnow()
            
            # Use OpenAI web search to find real businesses
            print("Searching for real businesses using OpenAI web search...")
            ai_response = self._search_and_analyze_with_web_search(campaign)
            
            # Parse AI response to extract company information
            leads_data = self._parse_ai_response(ai_response, campaign)
            
            # Process and validate leads
            processed_leads = self._process_leads_data(leads_data, campaign)
            
            # Update campaign with results
            campaign.total_found = len(processed_leads)
            campaign.completed_at = datetime.utcnow()
            campaign.status = LeadGenerationStatus.COMPLETED
            campaign.ai_analysis_summary = ai_response
            
            return {
                'success': True,
                'leads': processed_leads,
                'total_found': len(processed_leads),
                'ai_analysis': ai_response
            }
            
        except Exception as e:
            campaign.status = LeadGenerationStatus.FAILED
            campaign.completed_at = datetime.utcnow()
            return {
                'success': False,
                'error': f'Lead generation failed: {str(e)}'
            }
    
    def _build_lead_generation_prompt(self, campaign: LeadGenerationCampaign) -> str:
        """Build AI prompt based on campaign type"""
        
        base_prompt = f"""
        I need you to find potential customers for structured cabling and IT infrastructure services.
        
        Search Criteria:
        - Location: {campaign.postcode}
        - Distance: {campaign.distance_miles} miles radius
        - Maximum results: {campaign.max_results}
        """
        
        if campaign.prompt_type == 'it_msp_expansion':
            prompt = base_prompt + """
            
            Find IT/MSP businesses that:
            - Are within the specified area
            - Currently offer IT services but may not offer structured cabling
            - Would benefit from adding cabling services to their portfolio
            - Have the technical capability to expand into cabling work
            
            Focus on companies that:
            - Are established IT service providers
            - Have technical staff
            - Serve business customers
            - May be looking to expand their service offerings
            """
        
        elif campaign.prompt_type == 'it_msp_gaps':
            prompt = base_prompt + """
            
            Find IT/MSP businesses that:
            - Are within the specified area
            - Don't currently offer structured cabling services
            - Have gaps in their service portfolio
            - Could partner with or refer cabling work
            
            Look for companies that:
            - Offer IT support but not infrastructure installation
            - May be turning away cabling projects
            - Could benefit from a cabling partnership
            """
        
        elif campaign.prompt_type == 'similar_business':
            prompt = base_prompt + f"""
            
            Find businesses similar to: {campaign.company_name_filter}
            
            Look for companies that:
            - Have similar business models
            - Serve similar customer bases
            - Are in related industries
            - Have similar company sizes
            - May have similar IT infrastructure needs
            """
        
        elif campaign.prompt_type == 'competitor_verification':
            prompt = base_prompt + """
            
            VERIFY AND COLLECT DATA FOR IDENTIFIED COMPETITOR COMPANIES:
            
            This campaign is for verifying and collecting detailed information about specific competitor companies that have already been identified.
            
            IMPORTANT: You are NOT finding new companies - you are verifying existing ones.
            
            For each competitor company provided, verify and collect:
            - Confirmation that the company exists and is active
            - Current website URL and contact information
            - Business address and postcode
            - Companies House registration details
            - Current business status and services offered
            - Key personnel and decision makers
            - Recent business activities or news
            
            Focus on getting ACCURATE, CURRENT information for each competitor.
            """
        
        elif campaign.prompt_type == 'education':
            prompt = base_prompt + """
            
            Find educational institutions that:
            - Are within the specified area
            - May need network upgrades or new installations
            - Are planning technology improvements
            - Have aging IT infrastructure
            - Are expanding or renovating facilities
            
            Focus on:
            - Schools and colleges
            - Universities
            - Training centers
            - Educational technology companies
            """
        
        elif campaign.prompt_type == 'healthcare':
            prompt = base_prompt + """
            
            Find healthcare facilities that:
            - Are within the specified area
            - May need network upgrades for patient records
            - Are expanding or renovating
            - Have compliance requirements for secure networking
            - Are adopting new healthcare technologies
            
            Look for:
            - Hospitals and clinics
            - Medical practices
            - Dental offices
            - Veterinary clinics
            - Healthcare technology companies
            """
        
        elif campaign.prompt_type == 'new_businesses':
            prompt = base_prompt + """
            
            Find new businesses that:
            - Have opened in the last 6-12 months
            - Are within the specified area
            - Are likely to need IT infrastructure
            - Are growing or expanding
            - May not have established IT providers
            
            Focus on companies that:
            - Are setting up new offices
            - Are expanding operations
            - Are in technology-reliant industries
            - Have significant IT needs
            """
        
        elif campaign.prompt_type == 'planning_applications':
            prompt = base_prompt + """
            
            Find businesses that:
            - Have submitted planning applications recently
            - Are planning construction or renovation
            - Are expanding their facilities
            - Will need new IT infrastructure
            - Are within the specified area
            
            Look for companies that:
            - Are building new offices
            - Are renovating existing spaces
            - Are expanding manufacturing facilities
            - Are developing commercial properties
            """
        
        elif campaign.prompt_type == 'manufacturing':
            prompt = base_prompt + """
            
            Find manufacturing companies that:
            - Are within the specified area
            - Are modernizing their operations
            - Are implementing Industry 4.0 technologies
            - Need industrial networking solutions
            - Are expanding their facilities
            
            Focus on companies that:
            - Are upgrading their IT systems
            - Need industrial-grade networking
            - Are implementing IoT solutions
            - Have complex networking requirements
            """
        
        elif campaign.prompt_type == 'retail_office':
            prompt = base_prompt + """
            
            Find retail and office businesses that:
            - Are within the specified area
            - Are renovating or expanding
            - Need modern networking solutions
            - Are upgrading their IT infrastructure
            - Have multiple locations
            
            Look for companies that:
            - Are modernizing their spaces
            - Need point-of-sale networking
            - Are implementing digital solutions
            - Have customer-facing technology needs
            """
        
        else:  # custom prompt
            prompt = base_prompt + f"""
            
            Custom search criteria:
            {campaign.custom_prompt}
            """
        
        prompt += """
        
        IMPORTANT REQUIREMENTS:
        1. ONLY return REAL, VERIFIABLE businesses that exist in the UK
        2. Each business MUST be registered with Companies House
        3. Include Companies House registration numbers where possible
        4. Focus on businesses with active websites and real contact information
        5. Do NOT include fictional or example companies
        
        For each business you find, provide:
        1. Company name (exact name as registered)
        2. Companies House registration number (if known)
        3. Website (must be real and active)
        4. Brief description of why they would need cabling services
        5. Estimated project value (Small: <£10k, Medium: £10k-£50k, Large: >£50k)
        6. Timeline estimate (e.g., "Within 3 months", "Q1 2024", "Within 6 months")
        7. Contact information (if available)
        8. Lead score (0-100) based on likelihood to need services
        9. Business address and postcode
        
        Format your response as a JSON array with this structure:
        [
            {
                "company_name": "Real Company Name Ltd",
                "company_registration": "12345678",
                "website": "https://realcompany.com",
                "description": "Why they need cabling services",
                "project_value": "Medium",
                "timeline": "Within 3 months",
                "contact_name": "Real Contact Person",
                "contact_email": "contact@realcompany.com",
                "contact_phone": "01234 567890",
                "lead_score": 75,
                "address": "Real Business Address",
                "postcode": "LE17 5NJ",
                "business_sector": "IT Services",
                "company_size": "Small (1-10 employees)"
            }
        ]
        
        CRITICAL: Only include businesses you can verify exist. If you're unsure about a company, don't include it.
        """
        
        return prompt
    
    def _search_and_analyze_with_web_search(self, campaign: LeadGenerationCampaign) -> str:
        """Find real businesses using enhanced AI prompt with specific examples"""
        try:
            # Build search query based on campaign type
            search_query = self._build_web_search_query(campaign)
            
            # Create an enhanced prompt that focuses on real businesses
            prompt = f"""
            I need you to find real, existing UK businesses that would be good prospects for structured cabling and IT infrastructure services.

            SEARCH CRITERIA:
            - Location: {campaign.postcode} (within {campaign.distance_miles} miles radius)
            - Campaign Type: {campaign.prompt_type}
            - Target: {campaign.max_results} real businesses
            - Focus: Companies that need structured cabling, WiFi, CCTV, or IT infrastructure

            SEARCH STRATEGY:
            Look for businesses in these categories:
            """
            
            if campaign.prompt_type == 'it_msp_expansion':
                prompt += """
            - IT service companies that might expand into cabling
            - Managed service providers looking to add infrastructure services
            - Computer repair shops wanting to offer installation services
            - Software companies that need better office networks
            - Tech startups requiring office infrastructure
            """
            elif campaign.prompt_type == 'education':
                prompt += """
            - Primary and secondary schools needing network upgrades
            - Colleges requiring new IT infrastructure
            - Universities with campus expansion projects
            - Training centers needing better connectivity
            - Educational technology companies
            """
            elif campaign.prompt_type == 'manufacturing':
                prompt += """
            - Manufacturing companies modernizing facilities
            - Industrial businesses implementing IoT systems
            - Production facilities needing better connectivity
            - Engineering companies upgrading systems
            - Factory automation companies
            """
            elif campaign.prompt_type == 'retail_office':
                prompt += """
            - Retail stores needing point-of-sale networks
            - Office buildings requiring structured cabling
            - Commercial properties upgrading infrastructure
            - Business centers needing WiFi upgrades
            - Professional services firms expanding
            """
            
            prompt += f"""
            
            IMPORTANT: Use your comprehensive knowledge of UK businesses to find real, existing businesses in the {campaign.postcode} area that match these criteria.
            
            RETURN FORMAT - JSON array only:
            [
                {{
                    "company_name": "Real Company Name Ltd",
                    "website": "https://realcompany.com",
                    "description": "Specific reason they need cabling services",
                    "project_value": "Small/Medium/Large",
                    "timeline": "Within 3 months/6 months/1 year",
                    "contact_name": "Contact Person Name",
                    "contact_email": "contact@realcompany.com",
                    "contact_phone": "01234 567890",
                    "lead_score": 85,
                    "address": "Full business address",
                    "postcode": "{campaign.postcode}",
                    "business_sector": "Primary business sector",
                    "company_size": "Micro/Small/Medium/Large"
                }}
            ]

            CRITICAL REQUIREMENTS:
            1. Use your knowledge of REAL UK businesses that actually exist
            2. Focus on well-known companies, chains, franchises, and established businesses
            3. Include businesses you know exist from Companies House, business directories, or common knowledge
            4. Only include businesses in the {campaign.postcode} area
            5. Provide realistic contact information for known businesses
            6. Focus on businesses likely to need IT infrastructure
            7. Make lead scores realistic (60-95 range)
            8. Include examples like: major retailers, office buildings, schools, hospitals, manufacturing companies, etc.

            EXAMPLES OF REAL BUSINESSES TO CONSIDER:
            - Major retail chains (Tesco, Sainsbury's, etc.)
            - Office buildings and business centers
            - Schools and educational institutions
            - Healthcare facilities
            - Manufacturing companies
            - Professional services firms
            - Hotels and hospitality businesses
            - Government buildings and services

            Find real businesses for: {search_query}
            
            Return ONLY the JSON array, no additional text.
            """
            
            # Try the Responses API with web search first
            try:
                return self._use_responses_api_with_web_search(campaign)
            except Exception as e:
                # Convert exception to ASCII-safe string
                error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"Responses API failed, falling back to chat completions: {error_msg}")
                # Fallback to GPT-5 with enhanced knowledge base
                response = self.openai_client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a UK business development expert with extensive knowledge of real companies, business directories, and Companies House data. You must only return businesses that actually exist. Use your comprehensive knowledge of UK businesses to find real companies. Focus on companies that genuinely need structured cabling and IT infrastructure services."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    # temperature=0.4,  # GPT-5 only supports default temperature
                    max_completion_tokens=100000  # Large token limit for GPT-5 reasoning + comprehensive response
                )
                
                ai_response = response.choices[0].message.content
                print(f"AI Response received: {ai_response[:500]}...")  # Debug: show first 500 chars
                return ai_response
            
        except Exception as e:
            print(f"Error in enhanced search: {e}")
            # Fallback to basic search
            return self._fallback_basic_search(campaign)
    
    def _use_responses_api_with_web_search(self, campaign: LeadGenerationCampaign) -> str:
        """Use OpenAI Responses API with web search to find and analyze real businesses"""
        import json
        import re
        
        print(f"\n{'='*60}")
        print(f"STARTING GPT-5 WEB SEARCH FOR CAMPAIGN: {campaign.name}")
        print(f"Postcode: {campaign.postcode}")
        print(f"Distance: {campaign.distance_miles} miles")
        print(f"Max Results: {campaign.max_results}")
        print(f"Campaign Type: {campaign.prompt_type}")
        print(f"{'='*60}\n")
        
        # Define the output schema for structured results
        output_schema = {
            "type": "object",
            "properties": {
                "query_area": {"type": "string"},
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "company_name": {"type": "string"},
                            "website": {"type": ["string", "null"]},
                            "description": {"type": "string"},
                            "project_value": {"type": "string"},
                            "timeline": {"type": "string"},
                            "contact_name": {"type": ["string", "null"]},
                            "contact_email": {"type": ["string", "null"]},
                            "contact_phone": {"type": ["string", "null"]},
                            "lead_score": {"type": "number"},
                            "address": {"type": ["string", "null"]},
                            "postcode": {"type": "string"},
                            "business_sector": {"type": "string"},
                            "company_size": {"type": "string"}
                        },
                        "required": ["company_name", "website", "description", "postcode", "lead_score"]
                    }
                }
            },
            "required": ["query_area", "results"]
        }
        
        # Create the search prompt with detailed instructions
        system_prompt = """You are a UK business research specialist with access to live web search.
Your job is to find REAL, VERIFIED businesses that currently operate in the UK.

CRITICAL REQUIREMENTS:
1. Use web search to find actual UK businesses (search websites, directories, online listings)
2. Each business MUST have a real website or verifiable online presence
3. Verify UK postcodes are genuine and in the correct format
4. Only return businesses that are currently active and trading
5. Return ONLY valid JSON matching the exact schema provided
6. Do NOT make up or fabricate business information

SEARCH STRATEGY:
- Search for "{postcode} IT companies" or "{postcode} MSP" or similar relevant terms
- Look for business directories like Yell.com, Thomson Local, UK businesses directories
- Check business listings and review sites
- Verify websites are active and businesses are real
- Get actual contact information from websites when available
"""
        
        user_task = f"""
TASK: Find {campaign.max_results} REAL, VERIFIED UK businesses near {campaign.postcode} (within {campaign.distance_miles} miles).

Campaign Focus: {campaign.prompt_type}
Search Area: {campaign.postcode} + {campaign.distance_miles} miles radius

SEARCH APPROACH:
1. Start by searching: "{campaign.postcode} IT services companies" or "{campaign.postcode} managed service providers"
2. Look in UK business directories (Yell, Thomson Local, Google Business, etc.)
3. Check business listings and review sites (Trustpilot, Google Reviews)
4. Verify each business has:
   - Real website (check it exists and loads)
   - Valid UK postcode
   - Genuine contact information
   - Active business status

FOR EACH BUSINESS FOUND:
- Extract company name from their website
- Get their actual postcode from their website contact page
- Get real contact email/phone from their website
- **IMPORTANT**: If a business doesn't have a verifiable website, set website to null
- Note their business focus and services
- Assess if they would benefit from structured cabling services
- Provide lead score (60-95) based on how good a prospect they are

QUALITY OVER QUANTITY:
- Better to return 5 verified businesses than 20 fake ones
- Each business must be real and verifiable
- Include source URLs where you found the information
"""
        
        if campaign.prompt_type == 'it_msp_expansion':
            user_task += """
SPECIFIC BUSINESS TYPES TO FIND:
            [INCLUDE] IT Support Companies (MSP/Break-fix)
            [INCLUDE] Managed Service Providers
            [INCLUDE] Computer Repair Shops
            [INCLUDE] IT Consultancies
            [INCLUDE] Software Development Companies
            [INCLUDE] Web Design/Development Agencies
            [INCLUDE] Technology Resellers
            [INCLUDE] Computer Sales and Service
            [INCLUDE] Network Support Companies
            [INCLUDE] Cybersecurity Firms

            DO NOT INCLUDE:
            [EXCLUDE] Universities or Schools
            [EXCLUDE] Hospitals or Healthcare
            [EXCLUDE] Shopping Centers or Retail Stores
            [EXCLUDE] Councils or Government Buildings
            [EXCLUDE] Hotels or Hospitality
            [EXCLUDE] Theatres or Entertainment Venues
            [EXCLUDE] Libraries or Museums

FOCUS: Small to medium-sized IT businesses that currently serve customers but DON'T offer structured cabling installation themselves.
"""
        elif campaign.prompt_type == 'education':
            user_task += """
Look for:
- Primary and secondary schools needing network upgrades
- Colleges requiring new IT infrastructure
- Universities with campus expansion projects
- Training centers needing better connectivity
- Educational technology companies
"""
        elif campaign.prompt_type == 'manufacturing':
            user_task += """
Look for:
- Manufacturing companies modernizing facilities
- Industrial businesses implementing IoT systems
- Production facilities needing better connectivity
- Engineering companies upgrading systems
- Factory automation companies
"""
        elif campaign.prompt_type == 'retail_office':
            user_task += """
Look for:
- Retail stores needing point-of-sale networks
- Office buildings requiring structured cabling
- Commercial properties upgrading infrastructure
- Business centers needing WiFi upgrades
- Professional services firms expanding
"""
        
        print(f"Making GPT-5 Responses API call with web search...")
        print(f"Timeout set to: 180 seconds")
        
        try:
            # Use GPT-5-mini with Responses API and web search
            print("Using GPT-5-mini with Responses API and web search...")
            print(f"Model: gpt-5-mini")
            print(f"Max tokens: 50000")
            
            # Build comprehensive prompt (simpler format for GPT-5-mini)
            full_prompt = f"""{user_task}

OUTPUT FORMAT: Valid JSON matching this structure:
{{
  "query_area": "Leicester, UK",
  "results": [
    {{
      "company_name": "string",
      "website": "string or null",
      "description": "string",
      "project_value": "Small/Medium/Large",
      "timeline": "string",
      "contact_name": "string or null",
      "contact_email": "string or null",
      "contact_phone": "string or null",
      "lead_score": 85,
      "address": "string or null",
      "postcode": "string",
      "business_sector": "string",
      "company_size": "Micro/Small/Medium/Large"
    }}
  ]
}}

CRITICAL: Use web search to find REAL businesses. Output ONLY the JSON object. No markdown code fences. No explanations."""
            
            # Use Responses API with web search (response_format not supported here)
            response = self.openai_client.responses.create(
                model="gpt-5-mini",
                tools=[{"type": "web_search"}],  # Enable web search
                input=[
                    {"role": "system", "content": "You are a UK business research expert with web search access. Use web search to find REAL UK businesses. Output ONLY valid JSON matching the schema provided."},
                    {"role": "user", "content": full_prompt},
                    {"role": "user", "content": f"Output schema: {json.dumps(output_schema)}"},
                    {"role": "user", "content": "Output JSON only. No markdown fences, no prose. Use web search to find real businesses."}
                ],
                metadata={"task": f"lead_generation_{campaign.prompt_type}"}
            )
            
            print(f"[OK] GPT-5-mini Responses API call completed!")
            
            # Debug the response structure
            print(f"Response type: {type(response)}")
            print(f"Response attributes: {dir(response)}")
            
            # Extract response from Responses API format
            # The output is a list where the last item is the actual message
            ai_response = None
            
            if hasattr(response, 'output') and isinstance(response.output, list):
                print(f"[OK] Found 'output' attribute with {len(response.output)} items")
                
                # Find the last message in the output
                for item in reversed(response.output):
                    if hasattr(item, 'type') and item.type == 'message':
                        print(f"[OK] Found message item")
                        # Extract text from the message content
                        if hasattr(item, 'content') and isinstance(item.content, list):
                            for content_item in item.content:
                                if hasattr(content_item, 'text'):
                                    ai_response = content_item.text
                                    print(f"[OK] Extracted text from message ({len(ai_response)} chars)")
                                    break
                        break
            
            if not ai_response:
                print(f"[ERROR] Could not extract response from API!")
                print(f"Response output items: {len(response.output) if hasattr(response, 'output') else 'No output'}")
                if hasattr(response, 'output'):
                    print(f"Output types: {[item.type if hasattr(item, 'type') else type(item) for item in response.output[:5]]}")
                raise Exception("Could not extract response from Responses API")
            
            print(f"[OK] Extracted response ({len(ai_response)} characters)")
            print(f"Response preview: {ai_response[:300]}...")
            
            # Clean markdown fences if present
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```'):
                print("[WARN] Response has markdown fences, cleaning...")
                lines = cleaned_response.split('\n')
                if len(lines) > 2:
                    cleaned_response = '\n'.join(lines[1:-1]).strip()
                print(f"[OK] Cleaned response: {cleaned_response[:200]}...")
            
            # Validate JSON
            try:
                parsed = json.loads(cleaned_response)
                print(f"[OK] JSON is valid")
                if 'results' in parsed:
                    print(f"[OK] Found {len(parsed['results'])} businesses in results")
                return cleaned_response
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON parsing failed: {e}")
                print(f"Response content: {cleaned_response[:500]}")
                # Return the cleaned response anyway, let _parse_ai_response handle it
                return cleaned_response
            
        except Exception as e:
            # Convert exception to ASCII-safe string for Windows console
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"[ERROR] Error in Responses API call: {error_msg}")
            print(f"Error type: {type(e)}")
            import traceback
            tb = traceback.format_exc().encode('ascii', 'replace').decode('ascii')
            print(f"Traceback: {tb}")
            raise
    
    def _extract_json_from_responses_api(self, response) -> str:
        """Extract JSON string from Responses API response"""
        import json
        import re
        
        print(f"\nExtracting JSON from Responses API...")
        print(f"Response has output attribute: {hasattr(response, 'output')}")
        
        # Collect text parts from the response
        txt_parts = []
        
        if hasattr(response, 'output'):
            print(f"Output items count: {len(response.output)}")
            for idx, item in enumerate(response.output):
                item_type = getattr(item, "type", None)
                print(f"  Item {idx}: type={item_type}")
                
                if item_type == "message":
                    if hasattr(item, 'content'):
                        print(f"    Message has content with {len(item.content)} parts")
                        for c_idx, c in enumerate(item.content):
                            c_type = getattr(c, "type", None)
                            print(f"      Content {c_idx}: type={c_type}")
                            
                            if c_type == "output_text":
                                text = getattr(c, 'text', '')
                                print(f"        Text length: {len(text)}")
                                txt_parts.append(text)
        
        raw = "".join(txt_parts).strip()
        print(f"\nCombined raw text length: {len(raw)}")
        print(f"Raw text preview (first 500 chars):\n{raw[:500]}")
        
        if not raw:
            print(f"[WARN] Warning: No text extracted from response!")
            print(f"Full response object: {response}")
            return '{"query_area": "unknown", "results": []}'
        
        # Remove markdown fences if present
        cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw, flags=re.IGNORECASE)
        
        # Try to find JSON object in the text if it's surrounded by other text
        json_match = re.search(r'\{.*"results".*\}', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)
            print(f"Extracted JSON from surrounding text")
        
        print(f"Cleaned text length: {len(cleaned)}")
        
        # Validate JSON
        try:
            parsed = json.loads(cleaned)
            print(f"[OK] JSON is valid!")
            print(f"[OK] Keys: {list(parsed.keys())}")
            return cleaned
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {e}")
            print(f"Failed text (first 2000 chars):\n{cleaned[:2000]}")
            raise e
    
    def _build_web_search_query(self, campaign: LeadGenerationCampaign) -> str:
        """Build web search query based on campaign type"""
        base_location = f"{campaign.postcode} UK"
        
        if campaign.prompt_type == 'it_msp_expansion':
            return f"IT services companies {base_location} managed service providers"
        elif campaign.prompt_type == 'education':
            return f"schools colleges universities {base_location} education institutions"
        elif campaign.prompt_type == 'manufacturing':
            return f"manufacturing companies {base_location} industrial businesses"
        elif campaign.prompt_type == 'retail_office':
            return f"retail businesses offices {base_location} commercial companies"
        elif campaign.prompt_type == 'similar_business':
            return f"companies similar to {campaign.company_name_filter} {base_location}"
        elif campaign.prompt_type == 'competitor_verification':
            return f"competitor companies verification {base_location}"
        else:
            return f"businesses companies {base_location} structured cabling prospects"
    
    def _fallback_basic_search(self, campaign: LeadGenerationCampaign) -> str:
        """Fallback to basic AI generation without web search"""
        try:
            prompt = self._build_lead_generation_prompt(campaign)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business development expert. Please provide real, verifiable UK businesses only. Focus on companies that would need structured cabling services."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # temperature=0.7,  # GPT-5 only supports default temperature
                max_completion_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error in fallback search: {str(e)}"
    
    def _search_companies_house(self, campaign: LeadGenerationCampaign) -> List[Dict]:
        """Search Companies House for real businesses based on campaign criteria"""
        try:
            companies_data = []
            
            # Build search terms based on campaign type
            search_terms = self._build_companies_house_search_terms(campaign)
            
            for search_term in search_terms:
                print(f"Searching Companies House for: {search_term}")
                
                # Search Companies House API
                ch_results = self.external_data_service.search_companies_house_by_keywords(
                    search_term, 
                    postcode=campaign.postcode,
                    max_results=50
                )
                
                if ch_results['success'] and ch_results['data']:
                    companies_data.extend(ch_results['data'])
                    print(f"Found {len(ch_results['data'])} companies for '{search_term}'")
            
            # Remove duplicates based on company number
            seen_companies = set()
            unique_companies = []
            for company in companies_data:
                company_number = company.get('company_number')
                if company_number and company_number not in seen_companies:
                    seen_companies.add(company_number)
                    unique_companies.append(company)
            
            print(f"Total unique companies found: {len(unique_companies)}")
            return unique_companies
            
        except Exception as e:
            print(f"Error searching Companies House: {e}")
            return []
    
    def _build_companies_house_search_terms(self, campaign: LeadGenerationCampaign) -> List[str]:
        """Build search terms for Companies House based on campaign type"""
        base_terms = []
        
        if campaign.prompt_type == 'it_msp_expansion':
            base_terms = [
                'IT services',
                'computer services',
                'software development',
                'network services',
                'technology services',
                'managed services',
                'IT support'
            ]
        elif campaign.prompt_type == 'education':
            base_terms = [
                'education',
                'school',
                'college',
                'university',
                'academy',
                'learning'
            ]
        elif campaign.prompt_type == 'manufacturing':
            base_terms = [
                'manufacturing',
                'production',
                'engineering',
                'industrial',
                'factory'
            ]
        elif campaign.prompt_type == 'retail_office':
            base_terms = [
                'retail',
                'office',
                'commercial',
                'business services',
                'consulting'
            ]
        elif campaign.prompt_type == 'competitor_verification':
            base_terms = [
                'IT services',
                'computer services',
                'managed services',
                'technology services',
                'software development',
                'network services',
                'IT support'
            ]
        else:
            # Default search terms
            base_terms = [
                'services',
                'business',
                'company',
                'ltd',
                'limited'
            ]
        
        return base_terms
    
    def _analyze_companies_with_ai(self, companies_data: List[Dict], campaign: LeadGenerationCampaign) -> str:
        """Use AI to analyze and filter found companies"""
        try:
            # Build AI prompt for company analysis
            prompt = f"""
            I have found {len(companies_data)} real companies from Companies House. Please analyze these companies and identify which ones would be good prospects for structured cabling and IT infrastructure services.

            Campaign Criteria:
            - Location: {campaign.postcode} (within {campaign.distance_miles} miles)
            - Campaign Type: {campaign.prompt_type}
            - Max Results: {campaign.max_results}

            Company Data to Analyze:
            """
            
            # Add company information to prompt
            for i, company in enumerate(companies_data[:20]):  # Limit to first 20 for prompt size
                prompt += f"""
            Company {i+1}:
            - Name: {company.get('title', 'N/A')}
            - Number: {company.get('company_number', 'N/A')}
            - Status: {company.get('company_status', 'N/A')}
            - Type: {company.get('company_type', 'N/A')}
            - Address: {company.get('address_snippet', 'N/A')}
            - SIC Codes: {company.get('description', 'N/A')}
            """
            
            prompt += """
            
            Please analyze these companies and return ONLY the ones that would be good prospects for structured cabling services. For each prospect, provide:

            JSON format:
            [
                {
                    "company_name": "Exact company name from Companies House",
                    "company_registration": "Company number",
                    "business_sector": "Main business sector",
                    "company_size": "Estimated size (Micro/Small/Medium/Large)",
                    "lead_score": 85,
                    "description": "Why they would need cabling services",
                    "project_value": "Small/Medium/Large",
                    "timeline": "Estimated timeline",
                    "address": "Full address",
                    "postcode": "Postcode"
                }
            ]

            Focus on companies that:
            - Are active businesses
            - Have office/retail/manufacturing premises
            - Are likely to need IT infrastructure
            - Are within reasonable distance
            - Have potential for growth

            Return ONLY real companies from the list above. Do not create fictional companies.
            """
            
            # Get AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business development expert analyzing real companies from Companies House. You must only return companies that actually exist in the provided list. Do not create fictional companies."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # temperature=0.3,  # GPT-5 only supports default temperature
                max_completion_tokens=3000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            return ""
    
    def _process_ai_analyzed_companies(self, ai_analysis: str, campaign: LeadGenerationCampaign) -> List[Dict]:
        """Process AI-analyzed companies into lead data"""
        try:
            # Parse AI response
            leads_data = self._parse_ai_response(ai_analysis, campaign)
            
            # Process and enhance lead data
            processed_leads = self._process_leads_data(leads_data, campaign)
            
            return processed_leads
            
        except Exception as e:
            print(f"Error processing AI-analyzed companies: {e}")
            return []
    
    def _fallback_ai_generation(self, campaign: LeadGenerationCampaign) -> Dict[str, Any]:
        """Fallback to original AI generation if Companies House search fails"""
        try:
            # Use the original AI generation method
            prompt = self._build_lead_generation_prompt(campaign)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business development AI assistant. Please provide real, verifiable UK businesses only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # temperature=0.7,  # GPT-5 only supports default temperature
                max_completion_tokens=4000
            )
            
            ai_response = response.choices[0].message.content
            leads_data = self._parse_ai_response(ai_response, campaign)
            processed_leads = self._process_leads_data(leads_data, campaign)
            
            campaign.total_found = len(processed_leads)
            campaign.completed_at = datetime.utcnow()
            campaign.status = LeadGenerationStatus.COMPLETED
            campaign.ai_analysis_summary = ai_response
            
            return {
                'success': True,
                'leads': processed_leads,
                'total_found': len(processed_leads),
                'ai_analysis': ai_response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Fallback AI generation failed: {str(e)}'
            }
    
    def _parse_ai_response(self, ai_response: str, campaign: LeadGenerationCampaign) -> List[Dict]:
        """Parse AI response to extract structured lead data"""
        try:
            print(f"\nParsing AI response ({len(ai_response)} characters)...")
            print(f"Response preview: {ai_response[:200]}...")
            
            # Try to parse the entire response as JSON first
            try:
                response_obj = json.loads(ai_response)
                print(f"[OK] Parsed response as JSON object")
                
                # Check if it's the schema format with 'results' key
                if isinstance(response_obj, dict) and 'results' in response_obj:
                    leads_data = response_obj['results']
                    print(f"[OK] Found {len(leads_data)} leads in 'results' key")
                    return leads_data if isinstance(leads_data, list) else []
                # Check if it's a direct array
                elif isinstance(response_obj, list):
                    print(f"[OK] Found {len(response_obj)} leads in direct array")
                    return response_obj
                else:
                    print(f"[WARN] Unexpected JSON structure: {list(response_obj.keys() if isinstance(response_obj, dict) else response_obj)}")
                    return []
                    
            except json.JSONDecodeError as e:
                print(f"[WARN] Not valid JSON at root level: {e}")
                # Try to extract JSON array from the response
                json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if json_match:
                    leads_json = json_match.group(0)
                    leads_data = json.loads(leads_json)
                    print(f"[OK] Extracted array from text, found {len(leads_data)} leads")
                    return leads_data if isinstance(leads_data, list) else []
                else:
                    print("[ERROR] No JSON array found in response, trying text extraction")
                    return self._extract_leads_from_text(ai_response)
                    
        except Exception as e:
            print(f"[ERROR] Error parsing AI response: {e}")
            import traceback
            print(traceback.format_exc())
            # If all parsing fails, try to extract information using regex
            return self._extract_leads_from_text(ai_response)
    
    def _extract_leads_from_text(self, text: str) -> List[Dict]:
        """Fallback method to extract lead information from unstructured text"""
        leads = []
        lines = text.split('\n')
        
        current_lead = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_lead:
                    leads.append(current_lead)
                    current_lead = {}
                continue
            
            if 'company' in line.lower() and 'name' in line.lower():
                current_lead['company_name'] = line.split(':', 1)[-1].strip()
            elif 'website' in line.lower():
                current_lead['website'] = line.split(':', 1)[-1].strip()
            elif 'description' in line.lower():
                current_lead['description'] = line.split(':', 1)[-1].strip()
            elif 'contact' in line.lower() and 'email' in line.lower():
                current_lead['contact_email'] = line.split(':', 1)[-1].strip()
            elif 'contact' in line.lower() and 'phone' in line.lower():
                current_lead['contact_phone'] = line.split(':', 1)[-1].strip()
        
        if current_lead:
            leads.append(current_lead)
        
        return leads
    
    def _process_leads_data(self, leads_data: List[Dict], campaign: LeadGenerationCampaign) -> List[Dict]:
        """Process and enhance lead data"""
        processed_leads = []
        
        for lead_data in leads_data:
            try:
                # Enhance with external data
                enhanced_lead = self._enhance_lead_data(lead_data, campaign)
                
                # Validate and clean data
                validated_lead = self._validate_lead_data(enhanced_lead)
                
                if validated_lead:
                    processed_leads.append(validated_lead)
                    
            except Exception as e:
                print(f"Error processing lead {lead_data.get('company_name', 'Unknown')}: {e}")
                continue
        
        return processed_leads
    
    def _enhance_lead_data(self, lead_data: Dict, campaign: LeadGenerationCampaign) -> Dict:
        """Enhance lead data with external information"""
        company_name = lead_data.get('company_name', '')
        website = lead_data.get('website', '')
        
        if not company_name:
            return lead_data
        
        # Get external data
        external_data = self.external_data_service.get_comprehensive_company_data(
            company_name, website
        )
        
        if external_data['success']:
            data = external_data['data']
            
            # Add Companies House data
            if data.get('companies_house'):
                ch_data = data['companies_house']
                lead_data['company_registration'] = ch_data.get('company_number')
                lead_data['companies_house_data'] = ch_data
            
            # Add LinkedIn data
            if data.get('linkedin'):
                lead_data['linkedin_url'] = data['linkedin'].get('linkedin_url')
                lead_data['linkedin_data'] = data['linkedin']
            
            # Add website data
            if data.get('website'):
                lead_data['website_data'] = data['website']
        
        return lead_data
    
    def _validate_lead_data(self, lead_data: Dict) -> Optional[Dict]:
        """Validate and clean lead data with Companies House verification"""
        if not lead_data.get('company_name'):
            return None
        
        # Clean and validate company name
        company_name = lead_data.get('company_name', '').strip() if lead_data.get('company_name') else ''
        if len(company_name) < 2:
            return None
        
        lead_data['company_name'] = company_name
        
        # Validate email if provided
        email = lead_data.get('contact_email', '').strip() if lead_data.get('contact_email') else ''
        if email and not self._is_valid_email(email):
            lead_data['contact_email'] = None
        
        # Validate phone if provided
        phone = lead_data.get('contact_phone', '').strip() if lead_data.get('contact_phone') else ''
        if phone:
            lead_data['contact_phone'] = self._clean_phone_number(phone)
        
        # Skip Companies House verification during initial lead generation
        # This can be done later during AI analysis when converting to customer/prospect
        lead_data['registration_confirmed'] = False
        lead_data.pop('company_registration', None)  # Remove if present
        
        # Set default values
        lead_data['lead_score'] = lead_data.get('lead_score', 50)
        lead_data['timeline'] = lead_data.get('timeline', 'Unknown')
        lead_data['project_value'] = lead_data.get('project_value', 'Unknown')
        
        return lead_data
    
    def _verify_companies_house(self, company_name: str, company_number: str = None) -> Dict[str, Any]:
        """Verify company exists in Companies House"""
        try:
            ch_data = self.external_data_service.get_companies_house_data(company_name, company_number)
            if ch_data['success']:
                return {
                    'verified': True,
                    'data': ch_data['data']
                }
            else:
                return {
                    'verified': False,
                    'error': ch_data.get('error', 'Company not found')
                }
        except Exception as e:
            return {
                'verified': False,
                'error': str(e)
            }
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number"""
        # Remove all non-digit characters except + at the start
        cleaned = re.sub(r'[^\d+]', '', phone)
        # Add UK country code if missing
        if not cleaned.startswith('+') and not cleaned.startswith('0'):
            cleaned = '+44' + cleaned
        return cleaned
    
    def create_leads_from_campaign(self, campaign: LeadGenerationCampaign, leads_data: List[Dict]) -> Dict[str, Any]:
        """Create Lead records from processed lead data"""
        print(f"Creating leads from {len(leads_data)} lead data items")
        created_leads = []
        duplicates_found = 0
        
        for lead_data in leads_data:
            try:
                # Check for duplicates within the same campaign first
                existing_lead_in_campaign = Lead.query.filter_by(
                    campaign_id=campaign.id,
                    company_name=lead_data['company_name']
                ).first()
                if existing_lead_in_campaign:
                    duplicates_found += 1
                    print(f"[DEDUP] Skipping duplicate in same campaign: {lead_data['company_name']}")
                    continue
                
                # Check for duplicates across all campaigns (if not including existing customers)
                if not campaign.include_existing_customers:
                    # Check for existing leads
                    existing_lead_anywhere = Lead.query.filter_by(company_name=lead_data['company_name']).first()
                    if existing_lead_anywhere:
                        duplicates_found += 1
                        print(f"[DEDUP] Skipping duplicate across campaigns: {lead_data['company_name']}")
                        continue
                    
                    # Check for existing customers in CRM
                    from models_crm import Customer
                    existing_customer = Customer.query.filter_by(company_name=lead_data['company_name']).first()
                    if existing_customer:
                        duplicates_found += 1
                        print(f"[DEDUP] Skipping - already exists as customer: {lead_data['company_name']}")
                        continue
                
                # Create new lead
                lead = Lead(
                    campaign_id=campaign.id,
                    company_name=lead_data['company_name'],
                    website=lead_data.get('website'),
                    company_registration=lead_data.get('company_registration'),
                    contact_name=lead_data.get('contact_name'),
                    contact_email=lead_data.get('contact_email'),
                    contact_phone=lead_data.get('contact_phone'),
                    address=lead_data.get('address'),
                    postcode=lead_data.get('postcode'),
                    business_sector=lead_data.get('business_sector'),
                    company_size=lead_data.get('company_size'),
                    lead_score=lead_data.get('lead_score', 50),
                    qualification_reason=lead_data.get('description'),
                    potential_project_value=self._estimate_project_value(lead_data.get('project_value')),
                    timeline_estimate=lead_data.get('timeline'),
                    ai_analysis=lead_data.get('ai_analysis'),
                    ai_confidence_score=lead_data.get('ai_confidence_score'),
                    ai_recommendation=lead_data.get('ai_recommendation'),
                    linkedin_url=lead_data.get('linkedin_url'),
                    linkedin_data=lead_data.get('linkedin_data'),
                    companies_house_data=lead_data.get('companies_house_data'),
                    website_data=lead_data.get('website_data'),
                    created_by=campaign.created_by
                )
                
                db.session.add(lead)
                created_leads.append(lead)
                
            except Exception as e:
                print(f"Error creating lead {lead_data.get('company_name', 'Unknown')}: {e}")
                continue
        
        # Update campaign statistics
        campaign.leads_created = len(created_leads)
        campaign.duplicates_found = duplicates_found
        
        return {
            'success': True,
            'leads_created': len(created_leads),
            'duplicates_found': duplicates_found,
            'leads': created_leads
        }
    
    def _estimate_project_value(self, project_value_str: str) -> Optional[float]:
        """Estimate project value from string description"""
        if not project_value_str:
            return None
        
        project_value_str = project_value_str.lower()
        
        if 'small' in project_value_str:
            return 5000.0  # £5k average
        elif 'medium' in project_value_str:
            return 25000.0  # £25k average
        elif 'large' in project_value_str:
            return 75000.0  # £75k average
        else:
            return 15000.0  # Default medium value
