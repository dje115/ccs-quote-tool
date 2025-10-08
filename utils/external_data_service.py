#!/usr/bin/env python3
"""
External data service for LinkedIn and Companies House integration
"""

import requests
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
from models import APISettings

class ExternalDataService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.companies_house_api_key = self._get_api_key('companies_house')
    
    def _get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key from database settings"""
        try:
            from flask import current_app
            with current_app.app_context():
                setting = APISettings.query.filter_by(service_name=service_name).first()
                return setting.api_key if setting else None
        except Exception as e:
            print(f"Error getting API key for {service_name}: {e}")
            return None
    
    def get_linkedin_company_data(self, company_name: str, website: str = None) -> Dict[str, Any]:
        """
        Get LinkedIn company data using web scraping
        Note: This is a basic implementation. LinkedIn has anti-scraping measures.
        """
        try:
            linkedin_data = {
                'linkedin_url': None,
                'linkedin_followers': None,
                'linkedin_industry': None,
                'linkedin_company_size': None,
                'linkedin_description': None,
                'linkedin_website': None,
                'linkedin_headquarters': None,
                'linkedin_founded': None,
                'linkedin_specialties': None
            }
            
            # Try to find LinkedIn URL from website or search
            if website:
                # Check if website has LinkedIn link
                try:
                    response = self.session.get(website, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        linkedin_links = soup.find_all('a', href=re.compile(r'linkedin\.com/company'))
                        if linkedin_links:
                            linkedin_data['linkedin_url'] = linkedin_links[0]['href']
                except:
                    pass
            
            # Search for LinkedIn company page
            if not linkedin_data['linkedin_url']:
                search_query = f"site:linkedin.com/company {company_name}"
                try:
                    # This would require a proper search implementation
                    # For now, we'll construct a likely URL
                    company_slug = re.sub(r'[^a-zA-Z0-9]+', '-', company_name.lower()).strip('-')
                    linkedin_data['linkedin_url'] = f"https://www.linkedin.com/company/{company_slug}"
                except:
                    pass
            
            return {
                'success': True,
                'data': linkedin_data,
                'source': 'linkedin_scraping'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'LinkedIn data extraction failed: {str(e)}',
                'data': {}
            }
    
    def get_companies_house_data(self, company_name: str, company_number: str = None) -> Dict[str, Any]:
        """
        Get Companies House data using their API
        """
        try:
            companies_house_data = {
                'company_number': None,
                'company_status': None,
                'company_type': None,
                'date_of_creation': None,
                'registered_office_address': None,
                'sic_codes': None,
                'accounts': None,
                'officers': None,
                'filing_history': None
            }
            
            # Companies House API endpoint
            base_url = "https://api.company-information.service.gov.uk"
            
            # Check if API key is configured
            if not self.companies_house_api_key:
                print("Companies House API key not configured - skipping registration lookup")
                return {
                    'success': False,
                    'error': 'Companies House API key not configured',
                    'data': {}
                }
            
            # Set up headers with API key
            headers = {'Authorization': self.companies_house_api_key}
            
            if company_number:
                # Direct lookup by company number
                url = f"{base_url}/company/{company_number}"
            else:
                # Search by company name
                url = f"{base_url}/search/companies"
                params = {'q': company_name, 'items_per_page': 1}
                
                response = self.session.get(url, params=params, headers=headers, timeout=10)
                if response.status_code == 200:
                    search_results = response.json()
                    if search_results.get('items'):
                        company_number = search_results['items'][0]['company_number']
                        url = f"{base_url}/company/{company_number}"
                    else:
                        return {
                            'success': False,
                            'error': 'Company not found in Companies House',
                            'data': {}
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Companies House search failed: {response.status_code}',
                        'data': {}
                    }
            
            # Get company details
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                company_data = response.json()
                
                # Get additional accounts information
                accounts_info = self._get_detailed_accounts_info(company_number, headers)
                
                companies_house_data.update({
                    'company_number': company_data.get('company_number'),
                    'company_status': company_data.get('company_status'),
                    'company_type': company_data.get('type'),
                    'date_of_creation': company_data.get('date_of_creation'),
                    'registered_office_address': company_data.get('registered_office_address'),
                    'sic_codes': company_data.get('sic_codes'),
                    'accounts': company_data.get('accounts'),
                    'accounts_detail': accounts_info,
                    'officers': company_data.get('officers', {}).get('items', [])[:5],  # Limit to 5 officers
                    'filing_history': company_data.get('filing_history', {}).get('items', [])[:10]  # Limit to 10 recent filings
                })
                
                return {
                    'success': True,
                    'data': companies_house_data,
                    'source': 'companies_house_api'
                }
            else:
                return {
                    'success': False,
                    'error': f'Companies House API error: {response.status_code}',
                    'data': {}
                }
                
        except Exception as e:
                return {
                    'success': False,
                    'error': f'Companies House data extraction failed: {str(e)}',
                    'data': {}
                }
    
    def _get_detailed_accounts_info(self, company_number: str, headers: Dict) -> Dict[str, Any]:
        """Get detailed accounts information from Companies House including financial data"""
        try:
            base_url = "https://api.company-information.service.gov.uk"
            
            accounts_info = {
                'filing_date': None,
                'accounts_type': None,
                'company_size': None,
                'shareholders_funds': None,
                'net_assets': None,
                'current_assets': None,
                'current_liabilities': None,
                'cash_at_bank': None,
                'turnover': None,
                'gross_profit': None,
                'operating_profit': None,
                'profit_before_tax': None,
                'profit_after_tax': None,
                'employees': None,
                'period_start': None,
                'period_end': None,
                'estimated_revenue': None
            }
            
            # Get company accounts data
            accounts_url = f"{base_url}/company/{company_number}"
            response = self.session.get(accounts_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                company_data = response.json()
                accounts_data = company_data.get('accounts', {})
                
                # Extract accounts dates
                if accounts_data:
                    accounts_info['filing_date'] = accounts_data.get('last_accounts', {}).get('made_up_to')
                    accounts_info['period_start'] = accounts_data.get('accounting_reference_date', {}).get('day')
                    accounts_info['period_end'] = accounts_data.get('last_accounts', {}).get('period_end_on')
                    accounts_info['accounts_type'] = accounts_data.get('last_accounts', {}).get('type')
                
                # Try to get detailed financial data from UK Establishment endpoint
                uk_est_url = f"{base_url}/company/{company_number}/uk-establishments"
                try:
                    uk_response = self.session.get(uk_est_url, headers=headers, timeout=5)
                    if uk_response.status_code == 200:
                        uk_data = uk_response.json()
                        # Process UK establishment data if available
                except:
                    pass
            
            # Get filing history for detailed accounts
            filing_url = f"{base_url}/company/{company_number}/filing-history"
            params = {'category': 'accounts', 'items_per_page': 5}
            
            response = self.session.get(filing_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                filing_data = response.json()
                
                if filing_data.get('items'):
                    latest_filing = filing_data['items'][0]
                    
                    # Extract company size from description
                    description = latest_filing.get('description', '').lower()
                    if 'micro-entity' in description:
                        accounts_info['company_size'] = 'Micro-entity'
                        accounts_info['estimated_revenue'] = '£0 - £632K'
                    elif 'small' in description:
                        accounts_info['company_size'] = 'Small'
                        accounts_info['estimated_revenue'] = '£632K - £10.2M'
                    elif 'medium' in description:
                        accounts_info['company_size'] = 'Medium'
                        accounts_info['estimated_revenue'] = '£10.2M - £36M'
                    elif 'large' in description or 'group' in description:
                        accounts_info['company_size'] = 'Large'
                        accounts_info['estimated_revenue'] = '£36M+'
                    
                    # Try to extract financial data from annotations if available
                    annotations = latest_filing.get('annotations', [])
                    for annotation in annotations:
                        description = annotation.get('description', '').lower()
                        
                        # Look for financial figures in annotations
                        if 'shareholder' in description or 'equity' in description:
                            # Try to extract numbers
                            import re
                            numbers = re.findall(r'£?[\d,]+(?:\.\d{2})?', description)
                            if numbers:
                                accounts_info['shareholders_funds'] = numbers[0]
                        
                        if 'cash' in description:
                            numbers = re.findall(r'£?[\d,]+(?:\.\d{2})?', description)
                            if numbers:
                                accounts_info['cash_at_bank'] = numbers[0]
                        
                        if 'turnover' in description or 'revenue' in description:
                            numbers = re.findall(r'£?[\d,]+(?:\.\d{2})?', description)
                            if numbers:
                                accounts_info['turnover'] = numbers[0]
            
            # Get detailed officers/directors information
            officers_url = f"{base_url}/company/{company_number}/officers"
            try:
                officer_response = self.session.get(officers_url, headers=headers, timeout=5)
                if officer_response.status_code == 200:
                    officer_data = officer_response.json()
                    total_officers = officer_data.get('total_results', 0)
                    
                    # Estimate based on number of officers
                    if total_officers <= 2:
                        accounts_info['employees'] = '1-10'
                    elif total_officers <= 5:
                        accounts_info['employees'] = '11-50'
                    elif total_officers <= 10:
                        accounts_info['employees'] = '51-200'
                    else:
                        accounts_info['employees'] = '200+'
                    
                    # Extract active directors information
                    active_directors = []
                    officers = officer_data.get('items', [])
                    
                    for officer in officers[:10]:  # Limit to top 10 officers
                        # Check if officer is active
                        if officer.get('resigned_on'):
                            continue  # Skip resigned officers
                        
                        officer_info = {
                            'name': officer.get('name', '').title(),
                            'role': officer.get('officer_role', '').title(),
                            'appointed_on': officer.get('appointed_on'),
                            'nationality': officer.get('nationality', '').title(),
                            'occupation': officer.get('occupation', '').title(),
                            'country_of_residence': officer.get('country_of_residence', '').upper(),
                            'date_of_birth': None,
                            'address': None
                        }
                        
                        # Extract date of birth (month and year only for privacy)
                        dob = officer.get('date_of_birth', {})
                        if dob:
                            month = dob.get('month')
                            year = dob.get('year')
                            if year:
                                officer_info['date_of_birth'] = f"{month}/{year}" if month else str(year)
                        
                        # Extract address information
                        address = officer.get('address', {})
                        if address:
                            address_parts = []
                            if address.get('premises'):
                                address_parts.append(address['premises'])
                            if address.get('address_line_1'):
                                address_parts.append(address['address_line_1'])
                            if address.get('locality'):
                                address_parts.append(address['locality'])
                            if address.get('postal_code'):
                                address_parts.append(address['postal_code'])
                            officer_info['address'] = ', '.join(address_parts) if address_parts else None
                        
                        # Add additional useful information
                        if officer.get('identification'):
                            officer_info['identification_type'] = officer['identification'].get('identification_type')
                        
                        # Count other directorships
                        links = officer.get('links', {})
                        if links.get('officer'):
                            officer_link = links['officer']
                            if isinstance(officer_link, str):
                                officer_info['officer_id'] = officer_link.split('/')[-2]
                            elif isinstance(officer_link, dict) and officer_link.get('appointments'):
                                # Handle case where links is a dict with appointments URL
                                appt_url = officer_link['appointments']
                                if isinstance(appt_url, str):
                                    officer_info['officer_id'] = appt_url.split('/')[-2]
                        
                        active_directors.append(officer_info)
                    
                    accounts_info['active_directors'] = active_directors
                    accounts_info['total_active_directors'] = len(active_directors)
                    
            except Exception as e:
                print(f"Error getting officers: {e}")
                pass
            
            return accounts_info
            
        except Exception as e:
            print(f"Error getting detailed accounts: {e}")
            return {'error': f'Failed to get accounts info: {str(e)}'}
    
    def search_companies_house_by_keywords(self, search_term: str, postcode: str = None, max_results: int = 50) -> Dict[str, Any]:
        """Search Companies House by keywords and optional postcode"""
        try:
            if not self.companies_house_api_key:
                return {
                    'success': False,
                    'error': 'Companies House API key not configured',
                    'data': []
                }
            
            base_url = "https://api.company-information.service.gov.uk"
            search_url = f"{base_url}/search/companies"
            
            headers = {'Authorization': self.companies_house_api_key}
            params = {
                'q': search_term,
                'items_per_page': min(max_results, 100)
            }
            
            # Add postcode filter if provided
            if postcode:
                params['q'] = f"{search_term} {postcode}"
            
            response = self.session.get(search_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                search_results = response.json()
                companies = search_results.get('items', [])
                
                # Filter by postcode if provided
                if postcode and companies:
                    filtered_companies = []
                    for company in companies:
                        company_address = company.get('address_snippet', '').lower()
                        if postcode.lower() in company_address or any(
                            postcode.lower() in addr.lower() for addr in company.get('address', [])
                        ):
                            filtered_companies.append(company)
                    companies = filtered_companies
                
                return {
                    'success': True,
                    'data': companies[:max_results],
                    'total_results': search_results.get('total_results', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f'Companies House search failed: {response.status_code}',
                    'data': []
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Companies House search error: {str(e)}',
                'data': []
            }
    
    def get_web_company_data(self, company_name: str, website: str = None) -> Dict[str, Any]:
        """
        Get additional company data from their website
        """
        try:
            web_data = {
                'website_title': None,
                'website_description': None,
                'contact_info': None,
                'services': None,
                'social_media': None,
                'key_phrases': None
            }
            
            if website:
                try:
                    response = self.session.get(website, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract basic info
                        web_data['website_title'] = soup.title.string if soup.title else None
                        
                        # Extract meta description
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc:
                            web_data['website_description'] = meta_desc.get('content')
                        
                        # Extract contact information
                        contact_patterns = [
                            r'\b\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b',  # Phone numbers
                            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email addresses
                        ]
                        
                        text_content = soup.get_text()
                        contacts = []
                        for pattern in contact_patterns:
                            matches = re.findall(pattern, text_content)
                            contacts.extend(matches)
                        
                        web_data['contact_info'] = list(set(contacts))[:5]  # Unique contacts, max 5
                        
                        # Extract social media links
                        social_links = []
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if any(platform in href.lower() for platform in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']):
                                social_links.append(href)
                        
                        web_data['social_media'] = social_links[:10]  # Max 10 social links
                        
                        # Extract key phrases (simple keyword extraction)
                        words = re.findall(r'\b[a-zA-Z]{4,}\b', text_content.lower())
                        word_freq = {}
                        for word in words:
                            if word not in ['this', 'that', 'with', 'from', 'they', 'been', 'have', 'will', 'your', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other']:
                                word_freq[word] = word_freq.get(word, 0) + 1
                        
                        web_data['key_phrases'] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
                        
                except Exception as e:
                    print(f"Error scraping website {website}: {e}")
            
            return {
                'success': True,
                'data': web_data,
                'source': 'website_scraping'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Web data extraction failed: {str(e)}',
                'data': {}
            }
    
    def get_comprehensive_company_data(self, company_name: str, website: str = None, company_number: str = None) -> Dict[str, Any]:
        """
        Get comprehensive company data from all sources
        """
        try:
            results = {
                'linkedin': self.get_linkedin_company_data(company_name, website),
                'companies_house': self.get_companies_house_data(company_name, company_number),
                'website': self.get_web_company_data(company_name, website)
            }
            
            # Combine successful results
            combined_data = {
                'company_name': company_name,
                'website': website,
                'company_number': company_number,
                'data_sources': [],
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            for source, result in results.items():
                if result['success']:
                    combined_data[source] = result['data']
                    combined_data['data_sources'].append(result['source'])
            
            return {
                'success': True,
                'data': combined_data,
                'sources_used': combined_data['data_sources']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Comprehensive data extraction failed: {str(e)}',
                'data': {}
            }
