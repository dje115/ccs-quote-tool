#!/usr/bin/env python3
"""
AI-powered customer intelligence service.
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import APISettings
from models_crm import Customer, BusinessSector, CustomerStatus
from utils.external_data_service import ExternalDataService

class CustomerIntelligenceService:
    def __init__(self):
        self.openai_client = None
        self.external_data_service = ExternalDataService()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client from database settings"""
        try:
            openai_setting = APISettings.query.filter_by(service_name='openai').first()
            if openai_setting and openai_setting.api_key:
                import openai
                self.openai_client = openai.OpenAI(
                    api_key=openai_setting.api_key,
                    timeout=90.0  # Increased timeout for GPT-5
                )
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
    
    def analyze_company(self, company_name: str, website: str = None, description: str = None, external_data: Dict = None) -> Dict[str, Any]:
        """Analyze a company using AI to gather business intelligence"""
        if not self.openai_client:
            return {'error': 'OpenAI client not initialized'}
        
        try:
            # Prepare company information for AI analysis
            company_info = f"Company Name: {company_name}"
            if website:
                company_info += f"\nWebsite: {website}"
            if description:
                company_info += f"\nDescription: {description}"
            
            # Add external data if available
            if external_data:
                company_info += f"\n\nExternal Data Sources:"
                if external_data.get('linkedin'):
                    linkedin = external_data['linkedin']
                    company_info += f"\nLinkedIn Data:"
                    if linkedin.get('linkedin_url'):
                        company_info += f"\n- LinkedIn URL: {linkedin['linkedin_url']}"
                    if linkedin.get('linkedin_industry'):
                        company_info += f"\n- Industry: {linkedin['linkedin_industry']}"
                    if linkedin.get('linkedin_company_size'):
                        company_info += f"\n- Company Size: {linkedin['linkedin_company_size']}"
                    if linkedin.get('linkedin_description'):
                        company_info += f"\n- LinkedIn Description: {linkedin['linkedin_description']}"
                
                if external_data.get('companies_house'):
                    ch = external_data['companies_house']
                    company_info += f"\nCompanies House Data:"
                    if ch.get('company_number'):
                        company_info += f"\n- Company Number: {ch['company_number']}"
                    if ch.get('company_status'):
                        company_info += f"\n- Status: {ch['company_status']}"
                    if ch.get('company_type'):
                        company_info += f"\n- Type: {ch['company_type']}"
                    if ch.get('date_of_creation'):
                        company_info += f"\n- Founded: {ch['date_of_creation']}"
                    if ch.get('registered_office_address'):
                        company_info += f"\n- Registered Address: {ch['registered_office_address']}"
                    if ch.get('sic_codes'):
                        company_info += f"\n- SIC Codes: {ch['sic_codes']}"
                    
                    # Add detailed financial information
                    if ch.get('accounts_detail'):
                        accounts = ch['accounts_detail']
                        company_info += f"\n\nFinancial Information (from Companies House):"
                        if accounts.get('company_size'):
                            company_info += f"\n- Company Size: {accounts['company_size']}"
                        if accounts.get('estimated_revenue'):
                            company_info += f"\n- Estimated Revenue Range: {accounts['estimated_revenue']}"
                        
                        # Enhanced financial data display
                        if accounts.get('shareholders_funds'):
                            company_info += f"\n- Shareholders' Funds: {accounts['shareholders_funds']}"
                        if accounts.get('shareholders_funds_current') and accounts.get('shareholders_funds_previous'):
                            company_info += f"\n- Shareholders' Funds (Current): £{accounts['shareholders_funds_current']:,.0f}"
                            company_info += f"\n- Shareholders' Funds (Previous): £{accounts['shareholders_funds_previous']:,.0f}"
                            # Calculate change
                            change = accounts['shareholders_funds_current'] - accounts['shareholders_funds_previous']
                            change_pct = (change / accounts['shareholders_funds_previous']) * 100 if accounts['shareholders_funds_previous'] > 0 else 0
                            company_info += f"\n- Shareholders' Funds Change: {change:+.0f} ({change_pct:+.1f}%)"
                        
                        if accounts.get('cash_at_bank'):
                            company_info += f"\n- Cash at Bank: {accounts['cash_at_bank']}"
                        if accounts.get('cash_at_bank_current') and accounts.get('cash_at_bank_previous'):
                            company_info += f"\n- Cash at Bank (Current): £{accounts['cash_at_bank_current']:,.0f}"
                            company_info += f"\n- Cash at Bank (Previous): £{accounts['cash_at_bank_previous']:,.0f}"
                            # Calculate change
                            change = accounts['cash_at_bank_current'] - accounts['cash_at_bank_previous']
                            change_pct = (change / accounts['cash_at_bank_previous']) * 100 if accounts['cash_at_bank_previous'] > 0 else 0
                            company_info += f"\n- Cash Change: {change:+.0f} ({change_pct:+.1f}%)"
                        
                        if accounts.get('turnover'):
                            company_info += f"\n- Turnover: {accounts['turnover']}"
                        if accounts.get('turnover_current') and accounts.get('turnover_previous'):
                            company_info += f"\n- Turnover (Current): £{accounts['turnover_current']:,.0f}"
                            company_info += f"\n- Turnover (Previous): £{accounts['turnover_previous']:,.0f}"
                            # Calculate growth
                            growth = accounts['turnover_current'] - accounts['turnover_previous']
                            growth_pct = (growth / accounts['turnover_previous']) * 100 if accounts['turnover_previous'] > 0 else 0
                            company_info += f"\n- Revenue Growth: {growth:+.0f} ({growth_pct:+.1f}%)"
                        
                        # Enhanced employee information
                        if accounts.get('employees'):
                            company_info += f"\n- Estimated Employees: {accounts['employees']}"
                        if accounts.get('employee_count'):
                            company_info += f"\n- Employee Count: {accounts['employee_count']}"
                        if accounts.get('employee_range'):
                            company_info += f"\n- Employee Range: {accounts['employee_range']}"
                        
                        # Financial health and trends
                        if accounts.get('revenue_growth'):
                            company_info += f"\n- Revenue Growth Trend: {accounts['revenue_growth']}"
                        if accounts.get('profitability_trend'):
                            company_info += f"\n- Profitability Trend: {accounts['profitability_trend']}"
                        if accounts.get('financial_health_score'):
                            company_info += f"\n- Financial Health Score: {accounts['financial_health_score']}/100"
                        if accounts.get('years_of_data'):
                            company_info += f"\n- Years of Financial Data Available: {accounts['years_of_data']}"
                        
                        # Additional financial metrics
                        if accounts.get('net_assets'):
                            company_info += f"\n- Net Assets: {accounts['net_assets']}"
                        if accounts.get('current_assets'):
                            company_info += f"\n- Current Assets: {accounts['current_assets']}"
                        if accounts.get('current_liabilities'):
                            company_info += f"\n- Current Liabilities: {accounts['current_liabilities']}"
                        if accounts.get('profit_before_tax'):
                            company_info += f"\n- Profit Before Tax: {accounts['profit_before_tax']}"
                        if accounts.get('filing_date'):
                            company_info += f"\n- Last Accounts Filed: {accounts['filing_date']}"
                        
                        # Multi-year financial history
                        if accounts.get('detailed_financials'):
                            company_info += f"\n\nFinancial History (Last {len(accounts['detailed_financials'])} Years):"
                            for i, year_data in enumerate(accounts['detailed_financials'][:3]):  # Show last 3 years
                                year_label = "Current" if i == 0 else f"Year -{i}"
                                company_info += f"\n{year_label} Year ({year_data.get('filing_date', 'Unknown')}):"
                                if year_data.get('turnover'):
                                    company_info += f"\n  - Turnover: £{year_data['turnover']:,.0f}" if isinstance(year_data['turnover'], (int, float)) else f"\n  - Turnover: {year_data['turnover']}"
                                if year_data.get('shareholders_funds'):
                                    company_info += f"\n  - Shareholders' Funds: £{year_data['shareholders_funds']:,.0f}" if isinstance(year_data['shareholders_funds'], (int, float)) else f"\n  - Shareholders' Funds: {year_data['shareholders_funds']}"
                                if year_data.get('cash_at_bank'):
                                    company_info += f"\n  - Cash at Bank: £{year_data['cash_at_bank']:,.0f}" if isinstance(year_data['cash_at_bank'], (int, float)) else f"\n  - Cash at Bank: {year_data['cash_at_bank']}"
                                if year_data.get('profit_before_tax'):
                                    company_info += f"\n  - Profit Before Tax: £{year_data['profit_before_tax']:,.0f}" if isinstance(year_data['profit_before_tax'], (int, float)) else f"\n  - Profit Before Tax: {year_data['profit_before_tax']}"
                        
                        # Add active directors information
                        if accounts.get('active_directors'):
                            directors = accounts['active_directors']
                            company_info += f"\n\nActive Directors/Officers ({accounts.get('total_active_directors', len(directors))}):"
                            for i, director in enumerate(directors, 1):
                                company_info += f"\n\n{i}. {director.get('name', 'Unknown')}"
                                if director.get('role'):
                                    company_info += f"\n   Role: {director['role']}"
                                if director.get('appointed_on'):
                                    company_info += f"\n   Appointed: {director['appointed_on']}"
                                if director.get('occupation'):
                                    company_info += f"\n   Occupation: {director['occupation']}"
                                if director.get('nationality'):
                                    company_info += f"\n   Nationality: {director['nationality']}"
                                if director.get('country_of_residence'):
                                    company_info += f"\n   Residence: {director['country_of_residence']}"
                                if director.get('date_of_birth'):
                                    company_info += f"\n   Age: Born {director['date_of_birth']}"
                
                if external_data.get('website'):
                    web = external_data['website']
                    company_info += f"\nWebsite Data:"
                    if web.get('website_title'):
                        company_info += f"\n- Website Title: {web['website_title']}"
                    if web.get('website_description'):
                        company_info += f"\n- Website Description: {web['website_description']}"
                    if web.get('key_phrases'):
                        company_info += f"\n- Key Phrases: {', '.join([phrase[0] for phrase in web['key_phrases'][:10]])}"
                
                if external_data.get('google_maps'):
                    maps = external_data['google_maps']
                    company_info += f"\nGoogle Maps Location Data:"
                    if maps.get('locations'):
                        company_info += f"\n- Primary Locations: {len(maps['locations'])} found"
                        for i, location in enumerate(maps['locations'][:5]):  # Show first 5 locations
                            company_info += f"\n  Location {i+1}: {location.get('name', 'Unknown')}"
                            company_info += f"\n    Address: {location.get('address', 'N/A')}"
                            if location.get('phone'):
                                company_info += f"\n    Phone: {location['phone']}"
                            if location.get('rating'):
                                company_info += f"\n    Rating: {location['rating']}/5"
                    
                    if maps.get('additional_locations'):
                        company_info += f"\n- Additional Locations: {len(maps['additional_locations'])} found"
                        for i, location in enumerate(maps['additional_locations'][:3]):  # Show first 3 additional
                            company_info += f"\n  Additional {i+1}: {location.get('name', 'Unknown')}"
                            company_info += f"\n    Address: {location.get('address', 'N/A')}"
                    
                    if maps.get('addresses'):
                        company_info += f"\n- All Addresses Found: {len(maps['addresses'])}"
                        for addr in maps['addresses'][:5]:  # Show first 5 addresses
                            company_info += f"\n  - {addr}"
            
            prompt = f"""
            Analyze this company and provide comprehensive business intelligence:

            {company_info}

            Please provide a detailed analysis including:

            1. **Business Sector Classification**: Choose the most appropriate sector from: office, retail, industrial, healthcare, education, hospitality, manufacturing, technology, finance, government, other

            2. **Company Size Assessment**: Use the Companies House financial data to provide accurate estimates:
               - Number of employees (use the employee estimates from Companies House data if available)
               - Revenue range (use actual turnover data from Companies House if available, otherwise estimate)
               - Business size category (Small, Medium, Large, Enterprise)

            3. **Primary Business Activities**: Describe what this company does, their main products/services

            4. **Technology Maturity**: Assess their likely technology sophistication based on company size and financial data:
               - Basic: Simple IT needs, basic infrastructure
               - Intermediate: Some advanced systems, growing IT requirements
               - Advanced: Sophisticated IT infrastructure, multiple systems
               - Enterprise: Complex, integrated systems, dedicated IT teams

            5. **IT Budget Estimate**: Based on their revenue and company size, estimate their likely annual IT spending range

            6. **Financial Health Analysis**: Analyze the financial data from Companies House:
               - Comment on their profitability trend (Growing/Stable/Declining)
               - Assess their financial stability based on shareholders' funds and cash position
               - Evaluate revenue growth trends
               - Identify any financial risks or opportunities

            7. **Growth Potential**: Assess potential for business growth and expansion based on financial trends and company size

            8. **Technology Needs Prediction**: What structured cabling, networking, and security needs might they have based on their size and financial position?

            9. **Competitive Landscape**: Identify potential competitors or similar companies

            10. **Business Opportunities**: What opportunities exist for IT infrastructure projects given their financial capacity and growth trajectory?

            11. **Risk Factors**: What challenges or risks might affect their IT projects based on their financial position?

            12. **Address and Location Analysis**: Based on the company information and website data, identify:
                - Primary business address (if different from registered address)
                - ALL additional sites/locations mentioned on their website (look for multiple offices, branches, facilities)
                - Geographic spread of operations (cities, regions, counties they serve)
                - Any specific location requirements or constraints
                - Multiple office locations, branches, or facilities (companies often have 2-5 locations)
                - Service areas and coverage regions
                - Look carefully for location pages, contact pages, or "Our Locations" sections
                - Extract complete addresses including postcodes for each location

            Please respond in JSON format with these exact fields:
            {{
                "business_sector": "string (one of the sectors listed above)",
                "estimated_employees": number,
                "estimated_revenue": "string (revenue range)",
                "business_size_category": "string (Small/Medium/Large/Enterprise)",
                "primary_business_activities": "string (detailed description)",
                "technology_maturity": "string (Basic/Intermediate/Advanced/Enterprise)",
                "it_budget_estimate": "string (budget range)",
                "growth_potential": "string (High/Medium/Low)",
                "technology_needs": "string (predicted IT needs)",
                "competitors": "string (competitor analysis)",
                "opportunities": "string (business opportunities)",
                "risks": "string (risk factors)",
                "company_profile": "string (comprehensive company summary)",
                "primary_address": "string (main business address if different from registered)",
                "additional_sites": "string (list of additional locations/sites)",
                "location_analysis": "string (geographic spread and location requirements)",
                "company_registration": "string (ONLY include if found in Companies House data - DO NOT guess or make up numbers)",
                "financial_health_analysis": "string (detailed analysis of financial position, profitability trends, and stability)",
                "employee_analysis": "string (analysis of employee count and company size based on Companies House data)",
                "revenue_analysis": "string (analysis of turnover trends and revenue growth)",
                "profitability_assessment": "string (assessment of profitability trends and financial performance)"
            }}

            Focus on UK market context and be realistic in your assessments.
            """
            
            print(f"Making GPT-5 API call for customer analysis...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a business intelligence analyst specializing in UK companies and IT infrastructure needs. Provide accurate, realistic assessments based on company information. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=50000,  # Conservative token limit for reliable AI analysis
                timeout=180.0
            )
            
            print(f"GPT-5 API call successful, processing response...")
            result_text = response.choices[0].message.content
            print(f"Raw response: {result_text[:200]}...")
            analysis = json.loads(result_text)
            
            return {
                'success': True,
                'analysis': analysis,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response that failed to parse: {result_text}")
            return {
                'success': False,
                'error': f'AI returned invalid JSON: {str(e)}'
            }
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            
            # Check if it's an API error
            if hasattr(e, 'response'):
                print(f"API response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'unknown'}")
                print(f"API response body: {e.response.text if hasattr(e.response, 'text') else 'unknown'}")
            
            # Check for specific error types
            error_message = str(e)
            if "status: 500" in error_message:
                return {
                    'success': False,
                    'error': 'AI analysis failed: Server error (500). This may be due to token limit or API timeout. Please try again.'
                }
            elif "timeout" in error_message.lower():
                return {
                    'success': False,
                    'error': 'AI analysis failed: Request timeout. The analysis may be too complex. Please try again.'
                }
            elif "token" in error_message.lower():
                return {
                    'success': False,
                    'error': 'AI analysis failed: Token limit exceeded. Please try again.'
                }
            
            return {
                'success': False,
                'error': f'AI analysis failed: {str(e)}'
            }
    
    def enhance_customer_with_ai(self, customer: Customer, include_external_data: bool = True) -> Dict[str, Any]:
        """Enhance customer record with AI-generated intelligence and external data"""
        try:
            # Gather company information
            company_name = customer.company_name
            website = customer.website
            description = customer.ai_company_profile  # Use existing profile if available
            
            # Get external data if requested
            external_data = None
            if include_external_data:
                external_result = self.external_data_service.get_comprehensive_company_data(
                    company_name, website, customer.company_registration
                )
                if external_result['success']:
                    external_data = external_result['data']
            
            # Perform AI analysis with external data
            analysis_result = self.analyze_company(company_name, website, description, external_data)
            
            if not analysis_result.get('success'):
                return analysis_result
            
            analysis = analysis_result['analysis']
            
            # Update customer record with AI insights
            customer.business_sector = BusinessSector(analysis.get('business_sector', 'other'))
            customer.estimated_employees = analysis.get('estimated_employees')
            customer.estimated_revenue = analysis.get('estimated_revenue')
            customer.business_size_category = analysis.get('business_size_category')
            customer.primary_business_activities = analysis.get('primary_business_activities')
            customer.technology_maturity = analysis.get('technology_maturity')
            customer.it_budget_estimate = analysis.get('it_budget_estimate')
            customer.growth_potential = analysis.get('growth_potential')
            customer.ai_company_profile = analysis.get('company_profile')
            customer.ai_technology_needs = analysis.get('technology_needs')
            customer.ai_competitors = analysis.get('competitors')
            customer.ai_opportunities = analysis.get('opportunities')
            customer.ai_risks = analysis.get('risks')
            
            # Store address analysis
            customer.primary_address = analysis.get('primary_address')
            customer.additional_sites = analysis.get('additional_sites')
            customer.location_analysis = analysis.get('location_analysis')
            
            # Calculate lead score based on AI analysis
            customer.lead_score = self._calculate_lead_score(analysis)
            
            # Store the complete AI analysis as raw JSON
            customer.ai_analysis_raw = json.dumps(analysis)
            
            # Store external data if available
            if external_data:
                if external_data.get('linkedin'):
                    customer.linkedin_url = external_data['linkedin'].get('linkedin_url')
                    customer.linkedin_data = json.dumps(external_data['linkedin'])
                
                if external_data.get('companies_house'):
                    customer.companies_house_data = json.dumps(external_data['companies_house'])
                
                if external_data.get('website'):
                    customer.website_data = json.dumps(external_data['website'])
                
                if external_data.get('google_maps'):
                    customer.google_maps_data = json.dumps(external_data['google_maps'])
            
            return {
                'success': True,
                'updated_fields': [
                    'business_sector', 'estimated_employees', 'estimated_revenue',
                    'business_size_category', 'primary_business_activities',
                    'technology_maturity', 'it_budget_estimate', 'growth_potential',
                    'ai_company_profile', 'ai_technology_needs', 'ai_competitors',
                    'ai_opportunities', 'ai_risks', 'lead_score'
                ],
                'analysis': analysis,
                'external_data': external_data  # Include external data for registration checking
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to enhance customer: {str(e)}'
            }
    
    def _calculate_lead_score(self, analysis: Dict) -> int:
        """Calculate lead score (0-100) based on AI analysis"""
        try:
            score = 50  # Base score
            
            # Business size scoring
            size_category = analysis.get('business_size_category', '').lower()
            if size_category in ['large', 'enterprise']:
                score += 20
            elif size_category == 'medium':
                score += 10
            
            # Technology maturity scoring
            tech_maturity = analysis.get('technology_maturity', '').lower()
            if tech_maturity == 'enterprise':
                score += 15
            elif tech_maturity == 'advanced':
                score += 10
            elif tech_maturity == 'intermediate':
                score += 5
            
            # Growth potential scoring
            growth_potential = analysis.get('growth_potential', '').lower()
            if growth_potential == 'high':
                score += 15
            elif growth_potential == 'medium':
                score += 8
            
            # IT budget scoring (rough estimate)
            it_budget = analysis.get('it_budget_estimate', '').lower()
            if '50k' in it_budget or '100k' in it_budget or '1m' in it_budget:
                score += 10
            elif '10k' in it_budget or '25k' in it_budget:
                score += 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            print(f"Error calculating lead score: {e}")
            return 50
    
    def suggest_technology_solutions(self, customer: Customer) -> Dict[str, Any]:
        """Suggest technology solutions based on customer profile"""
        if not self.openai_client:
            return {'error': 'OpenAI client not initialized'}
        
        try:
            customer_profile = {
                'company_name': customer.company_name,
                'business_sector': customer.business_sector.value if customer.business_sector else None,
                'estimated_employees': customer.estimated_employees,
                'business_size_category': customer.business_size_category,
                'technology_maturity': customer.technology_maturity,
                'primary_business_activities': customer.primary_business_activities,
                'ai_technology_needs': customer.ai_technology_needs
            }
            
            prompt = f"""
            Based on this customer profile, suggest specific technology solutions for structured cabling, networking, and security:

            Customer Profile:
            {json.dumps(customer_profile, indent=2)}

            Please suggest:

            1. **Structured Cabling Solutions**:
               - Cable types (Cat5e, Cat6, Cat6A, Fiber)
               - Network topology recommendations
               - Infrastructure requirements

            2. **WiFi Solutions**:
               - Access point recommendations
               - Coverage planning
               - Security considerations

            3. **CCTV/Security Solutions**:
               - Camera types and placement
               - Recording and monitoring systems
               - Access control systems

            4. **Door Entry Solutions**:
               - Entry system types
               - Integration possibilities

            5. **Priority Recommendations**:
               - What should be implemented first
               - Estimated project phases
               - Budget considerations

            Respond in JSON format:
            {{
                "cabling_recommendations": {{
                    "cable_types": ["string"],
                    "topology": "string",
                    "infrastructure": "string"
                }},
                "wifi_recommendations": {{
                    "access_points": "string",
                    "coverage_plan": "string",
                    "security": "string"
                }},
                "cctv_recommendations": {{
                    "camera_types": "string",
                    "placement": "string",
                    "monitoring": "string"
                }},
                "door_entry_recommendations": {{
                    "system_types": "string",
                    "integration": "string"
                }},
                "implementation_priority": {{
                    "phase_1": "string",
                    "phase_2": "string",
                    "phase_3": "string"
                }},
                "budget_estimates": {{
                    "low_range": "string",
                    "high_range": "string",
                    "justification": "string"
                }}
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a technology consultant specializing in structured cabling, networking, and security solutions. Provide practical, cost-effective recommendations. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                # temperature=0.4,  # GPT-5 only supports default temperature
                max_completion_tokens=2000,
                # response_format={"type": "json_object"}  # GPT-5 may not support this parameter
            )
            
            result_text = response.choices[0].message.content
            recommendations = json.loads(result_text)
            
            return {
                'success': True,
                'recommendations': recommendations,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate recommendations: {str(e)}'
            }
    
    def analyze_competitors(self, customer: Customer) -> Dict[str, Any]:
        """Analyze competitors and market positioning"""
        if not self.openai_client:
            return {'error': 'OpenAI client not initialized'}
        
        try:
            company_info = f"""
            Company: {customer.company_name}
            Sector: {customer.business_sector.value if customer.business_sector else 'Unknown'}
            Activities: {customer.primary_business_activities or 'Unknown'}
            Size: {customer.business_size_category or 'Unknown'}
            """
            
            prompt = f"""
            Analyze the competitive landscape for this UK company:

            {company_info}

            Provide:

            1. **Direct Competitors**: Companies offering similar products/services
            2. **Market Position**: Where they likely sit in their market
            3. **Competitive Advantages**: What might give them an edge
            4. **Market Challenges**: Potential threats or challenges
            5. **Industry Trends**: Relevant trends affecting their sector

            Respond in JSON format:
            {{
                "direct_competitors": ["competitor1", "competitor2", "competitor3"],
                "market_position": "string",
                "competitive_advantages": "string",
                "market_challenges": "string",
                "industry_trends": "string",
                "market_opportunities": "string"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a market analyst specializing in UK business markets. Provide accurate competitive analysis. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                # temperature=0.3,  # GPT-5 only supports default temperature
                max_completion_tokens=1500,
                # response_format={"type": "json_object"}  # GPT-5 may not support this parameter
            )
            
            result_text = response.choices[0].message.content
            analysis = json.loads(result_text)
            
            return {
                'success': True,
                'competitive_analysis': analysis,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Competitive analysis failed: {str(e)}'
            }
