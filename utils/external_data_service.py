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
    
    def _parse_ixbrl_document(self, content: str) -> Dict[str, Any]:
        """Parse iXBRL document to extract financial data"""
        try:
            import xml.etree.ElementTree as ET
            import re
            
            financial_data = {}
            
            # Parse the XML content
            root = ET.fromstring(content)
            
            # Define namespace mappings for iXBRL
            namespaces = {
                'ix': 'http://www.xbrl.org/2013/inlineXBRL',
                'xbrli': 'http://www.xbrl.org/2003/instance',
                'core': 'http://xbrl.frc.org.uk/fr/2023-01-01/core',
                'bus': 'http://xbrl.frc.org.uk/general/2023-01-01/common'
            }
            
            # Extract financial data using XBRL tags
            # Net Assets / Shareholders' Funds
            net_assets_elements = root.findall('.//ix:nonFraction[@name="core:NetAssetsLiabilities"]', namespaces)
            if net_assets_elements:
                # Get the most recent year's data (usually the first one)
                for elem in net_assets_elements[:1]:
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_data['net_assets'] = value
                        break
                    except:
                        continue
            
            # Cash at Bank
            cash_elements = root.findall('.//ix:nonFraction[@name="core:CashBankOnHand"]', namespaces)
            if cash_elements:
                for elem in cash_elements[:1]:
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_data['cash_at_bank'] = value
                        break
                    except:
                        continue
            
            # Total Equity
            equity_elements = root.findall('.//ix:nonFraction[@name="core:Equity"]', namespaces)
            if equity_elements:
                for elem in equity_elements[:1]:
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_data['total_equity'] = value
                        break
                    except:
                        continue
            
            # Property, Plant & Equipment
            ppe_elements = root.findall('.//ix:nonFraction[@name="core:PropertyPlantEquipment"]', namespaces)
            if ppe_elements:
                for elem in ppe_elements[:1]:
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_data['ppe'] = value
                        break
                    except:
                        continue
            
            # Trade Debtors
            debtors_elements = root.findall('.//ix:nonFraction[@name="core:TradeDebtorsTradeReceivables"]', namespaces)
            if debtors_elements:
                for elem in debtors_elements[:1]:
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_data['trade_debtors'] = value
                        break
                    except:
                        continue
            
            # Other Debtors
            other_debtors_elements = root.findall('.//ix:nonFraction[@name="core:OtherDebtors"]', namespaces)
            if other_debtors_elements:
                for elem in other_debtors_elements[:1]:
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_data['other_debtors'] = value
                        break
                    except:
                        continue
            
            # Average Number of Employees
            employees_elements = root.findall('.//ix:nonFraction[@name="core:AverageNumberEmployeesDuringPeriod"]', namespaces)
            if employees_elements:
                for elem in employees_elements[:1]:
                    try:
                        value = int(float(elem.text))
                        financial_data['employees'] = value
                        break
                    except:
                        continue
            
            # Share Capital - use a simpler approach
            share_capital_elements = root.findall('.//ix:nonFraction[@name="core:Equity"]', namespaces)
            if share_capital_elements:
                for elem in share_capital_elements[:1]:
                    try:
                        value = float(elem.text.replace(',', ''))
                        financial_data['share_capital'] = value
                        break
                    except:
                        continue
            
            # Try alternative parsing if XBRL tags don't work
            if not financial_data:
                # Fallback: parse using regex patterns on the text content
                financial_data = self._extract_financial_data_regex(content)
            
            return financial_data
            
        except Exception as e:
            print(f"Error parsing iXBRL document: {e}")
            return {}
    
    def _extract_financial_data_regex(self, content: str) -> Dict[str, Any]:
        """Extract financial data using regex patterns as fallback"""
        try:
            financial_data = {}
            import re
            
            # Look for financial figures in the content using regex
            patterns = {
                'net_assets': [r'Net assets.*?£([\d,]+)', r'Total equity.*?£([\d,]+)'],
                'cash_at_bank': [r'Cash at bank.*?£([\d,]+)', r'CashBankOnHand.*?([\d,]+)'],
                'trade_debtors': [r'Trade debtors.*?£([\d,]+)', r'TradeDebtors.*?([\d,]+)'],
                'employees': [r'Average.*?employees.*?(\d+)', r'AverageNumberEmployees.*?(\d+)'],
                'share_capital': [r'Share capital.*?£([\d,]+)', r'Called up share capital.*?£([\d,]+)']
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        try:
                            if key == 'employees':
                                financial_data[key] = int(matches[0])
                            else:
                                financial_data[key] = float(matches[0].replace(',', ''))
                            break
                        except:
                            continue
            
            return financial_data
            
        except Exception as e:
            print(f"Error in regex extraction: {e}")
            return {}
    
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
                'shareholders_funds_current': None,
                'shareholders_funds_previous': None,
                'net_assets': None,
                'current_assets': None,
                'current_liabilities': None,
                'cash_at_bank': None,
                'cash_at_bank_current': None,
                'cash_at_bank_previous': None,
                'turnover': None,
                'turnover_current': None,
                'turnover_previous': None,
                'gross_profit': None,
                'operating_profit': None,
                'profit_before_tax': None,
                'profit_after_tax': None,
                'employees': None,
                'employee_count': None,
                'employee_range': None,
                'period_start': None,
                'period_end': None,
                'estimated_revenue': None,
                'revenue_growth': None,
                'profitability_trend': None,
                'financial_health_score': None,
                'years_of_data': None,
                'detailed_financials': []
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
            
            # Get filing history for detailed accounts - get more years for trend analysis
            filing_url = f"{base_url}/company/{company_number}/filing-history"
            params = {'category': 'accounts', 'items_per_page': 10}  # Get up to 10 years
            
            response = self.session.get(filing_url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                filing_data = response.json()
                
                if filing_data.get('items'):
                    # Process multiple years of data
                    financial_history = []
                    
                    for i, filing in enumerate(filing_data['items'][:5]):  # Process last 5 years
                        year_data = {
                            'filing_date': filing.get('date'),
                            'description': filing.get('description', ''),
                            'shareholders_funds': None,
                            'cash_at_bank': None,
                            'turnover': None,
                            'profit_before_tax': None,
                            'employees': None,
                            'company_size': None
                        }
                        
                        # Extract company size from description
                        description = filing.get('description', '').lower()
                        if 'micro-entity' in description:
                            year_data['company_size'] = 'Micro-entity'
                            if i == 0:  # Latest year
                                accounts_info['company_size'] = 'Micro-entity'
                                accounts_info['estimated_revenue'] = '£0 - £632K'
                        elif 'small' in description:
                            year_data['company_size'] = 'Small'
                            if i == 0:
                                accounts_info['company_size'] = 'Small'
                                accounts_info['estimated_revenue'] = '£632K - £10.2M'
                        elif 'medium' in description:
                            year_data['company_size'] = 'Medium'
                            if i == 0:
                                accounts_info['company_size'] = 'Medium'
                                accounts_info['estimated_revenue'] = '£10.2M - £36M'
                        elif 'large' in description or 'group' in description:
                            year_data['company_size'] = 'Large'
                            if i == 0:
                                accounts_info['company_size'] = 'Large'
                                accounts_info['estimated_revenue'] = '£36M+'
                        
                        # Extract financial data from iXBRL documents
                        try:
                            import re
                            import xml.etree.ElementTree as ET
                            
                            # Get the filing document details
                            document_url = f"{base_url}/company/{company_number}/filing-history/{filing.get('transaction_id')}"
                            doc_response = self.session.get(document_url, headers=headers, timeout=15)
                            
                            if doc_response.status_code == 200:
                                doc_data = doc_response.json()
                                
                                # Try to access the iXBRL document directly
                                links = doc_data.get('links', {})
                                document_metadata_url = links.get('document_metadata')
                                
                                if document_metadata_url:
                                    try:
                                        # Get document metadata to find the iXBRL download URL
                                        metadata_response = self.session.get(document_metadata_url, headers=headers, timeout=10)
                                        if metadata_response.status_code == 200:
                                            metadata = metadata_response.json()
                                            
                                            # Look for document download links
                                            doc_links = metadata.get('links', {})
                                            if 'document' in doc_links:
                                                doc_url = doc_links['document']
                                                
                                                # Try to download the iXBRL document
                                                doc_response = self.session.get(doc_url, headers=headers, timeout=30)
                                                if doc_response.status_code == 200:
                                                    content_type = doc_response.headers.get('content-type', '')
                                                    
                                                    if 'xml' in content_type or 'html' in content_type:
                                                        # It's likely an iXBRL document
                                                        content = doc_response.text
                                                        print(f"[IXBRL] Found iXBRL document for {company_number}, size: {len(content)} chars")
                                                        
                                                        # Parse the iXBRL document for financial data
                                                        financial_data = self._parse_ixbrl_document(content)
                                                        
                                                        if financial_data:
                                                            # Extract key financial figures
                                                            if 'net_assets' in financial_data:
                                                                year_data['shareholders_funds'] = financial_data['net_assets']
                                                                if i == 0:
                                                                    accounts_info['shareholders_funds_current'] = financial_data['net_assets']
                                                                    accounts_info['shareholders_funds'] = f"£{financial_data['net_assets']:,.0f}"
                                                                elif i == 1:
                                                                    accounts_info['shareholders_funds_previous'] = financial_data['net_assets']
                                                            
                                                            if 'cash_at_bank' in financial_data:
                                                                year_data['cash_at_bank'] = financial_data['cash_at_bank']
                                                                if i == 0:
                                                                    accounts_info['cash_at_bank_current'] = financial_data['cash_at_bank']
                                                                    accounts_info['cash_at_bank'] = f"£{financial_data['cash_at_bank']:,.0f}"
                                                                elif i == 1:
                                                                    accounts_info['cash_at_bank_previous'] = financial_data['cash_at_bank']
                                                            
                                                            if 'total_equity' in financial_data:
                                                                year_data['total_equity'] = financial_data['total_equity']
                                                            
                                                            if 'employees' in financial_data:
                                                                year_data['employees'] = financial_data['employees']
                                                                if i == 0:
                                                                    accounts_info['employee_count'] = financial_data['employees']
                                                            
                                                            if 'trade_debtors' in financial_data:
                                                                year_data['trade_debtors'] = financial_data['trade_debtors']
                                                            
                                                            print(f"[IXBRL] Extracted financial data: {financial_data}")
                                                        else:
                                                            print(f"[IXBRL] No financial data extracted from document")
                                    except Exception as meta_e:
                                        print(f"Error accessing iXBRL document: {meta_e}")
                            
                            # Fallback: Try to extract from filing description if no iXBRL data found
                            if not any([year_data.get('shareholders_funds'), year_data.get('cash_at_bank')]):
                                description = filing.get('description', '').lower()
                                
                                # Look for financial figures in the description
                                financial_figures = re.findall(r'£([\d,]+(?:\.\d{2})?)', description)
                                if financial_figures:
                                    try:
                                        # Convert to numbers and find the largest (likely to be turnover)
                                        figure_values = [float(f.replace(',', '')) for f in financial_figures]
                                        largest_figure = max(figure_values)
                                        
                                        # Only use if it's a reasonable amount (not just a small fee)
                                        if largest_figure > 1000:
                                            year_data['turnover'] = largest_figure
                                            if i == 0:
                                                accounts_info['turnover_current'] = largest_figure
                                                accounts_info['turnover'] = f"£{largest_figure:,.0f}"
                                            elif i == 1:
                                                accounts_info['turnover_previous'] = largest_figure
                                    except:
                                        pass
                            
                            # Log what we found for debugging
                            if any([year_data.get('turnover'), year_data.get('shareholders_funds'), year_data.get('cash_at_bank')]):
                                print(f"[FINANCIAL] Found financial data for {company_number} year {i}: {year_data}")
                            else:
                                print(f"[FINANCIAL] No financial data found for {company_number} year {i}")
                        
                        except Exception as e:
                            print(f"Error extracting financial data: {e}")
                        
                        financial_history.append(year_data)
                    
                    accounts_info['detailed_financials'] = financial_history
                    accounts_info['years_of_data'] = len(financial_history)
                    
                    # Calculate trends and growth
                    if len(financial_history) >= 2:
                        current = financial_history[0]
                        previous = financial_history[1]
                        
                        # Calculate revenue growth
                        if current.get('turnover') and previous.get('turnover'):
                            try:
                                current_rev = float(current['turnover']) if isinstance(current['turnover'], (int, float)) else float(str(current['turnover']).replace(',', ''))
                                previous_rev = float(previous['turnover']) if isinstance(previous['turnover'], (int, float)) else float(str(previous['turnover']).replace(',', ''))
                                if previous_rev > 0:
                                    growth = ((current_rev - previous_rev) / previous_rev) * 100
                                    accounts_info['revenue_growth'] = f"{growth:+.1f}%"
                            except:
                                pass
                        
                        # Calculate profitability trend
                        if current.get('shareholders_funds') and previous.get('shareholders_funds'):
                            try:
                                current_funds = float(current['shareholders_funds']) if isinstance(current['shareholders_funds'], (int, float)) else float(str(current['shareholders_funds']).replace(',', ''))
                                previous_funds = float(previous['shareholders_funds']) if isinstance(previous['shareholders_funds'], (int, float)) else float(str(previous['shareholders_funds']).replace(',', ''))
                                if current_funds > previous_funds:
                                    accounts_info['profitability_trend'] = 'Growing'
                                elif current_funds < previous_funds:
                                    accounts_info['profitability_trend'] = 'Declining'
                                else:
                                    accounts_info['profitability_trend'] = 'Stable'
                            except:
                                pass
                        
                        # Calculate financial health score (simple scoring system)
                        health_score = 50  # Base score
                        
                        # Revenue growth bonus
                        if accounts_info.get('revenue_growth'):
                            try:
                                growth_pct = float(accounts_info['revenue_growth'].replace('%', '').replace('+', ''))
                                if growth_pct > 10:
                                    health_score += 20
                                elif growth_pct > 0:
                                    health_score += 10
                                elif growth_pct > -5:
                                    health_score += 5
                                else:
                                    health_score -= 10
                            except:
                                pass
                        
                        # Profitability trend bonus
                        if accounts_info.get('profitability_trend') == 'Growing':
                            health_score += 15
                        elif accounts_info.get('profitability_trend') == 'Stable':
                            health_score += 5
                        elif accounts_info.get('profitability_trend') == 'Declining':
                            health_score -= 10
                        
                        accounts_info['financial_health_score'] = min(100, max(0, health_score))
            
            # Get detailed officers/directors information and better employee estimation
            officers_url = f"{base_url}/company/{company_number}/officers"
            try:
                officer_response = self.session.get(officers_url, headers=headers, timeout=5)
                if officer_response.status_code == 200:
                    officer_data = officer_response.json()
                    total_officers = officer_data.get('total_results', 0)
                    
                    # Enhanced employee estimation based on multiple factors
                    estimated_employees = None
                    employee_range = None
                    
                    # Factor 1: Number of officers (directors/managers)
                    if total_officers <= 2:
                        base_estimate = '1-10'
                        employee_range = '1-10'
                    elif total_officers <= 3:
                        base_estimate = '5-25'
                        employee_range = '5-25'
                    elif total_officers <= 5:
                        base_estimate = '11-50'
                        employee_range = '11-50'
                    elif total_officers <= 8:
                        base_estimate = '51-100'
                        employee_range = '51-100'
                    elif total_officers <= 15:
                        base_estimate = '101-200'
                        employee_range = '101-200'
                    else:
                        base_estimate = '200+'
                        employee_range = '200+'
                    
                    # Factor 2: Company size from accounts (more reliable)
                    if accounts_info.get('company_size'):
                        size = accounts_info['company_size']
                        if size == 'Micro-entity':
                            estimated_employees = '1-10'
                            employee_range = '1-10'
                        elif size == 'Small':
                            estimated_employees = '11-50'
                            employee_range = '11-50'
                        elif size == 'Medium':
                            estimated_employees = '51-250'
                            employee_range = '51-250'
                        elif size == 'Large':
                            estimated_employees = '250+'
                            employee_range = '250+'
                    
                    # Factor 3: Revenue-based estimation (if available)
                    if accounts_info.get('turnover_current'):
                        try:
                            turnover = float(accounts_info['turnover_current'])
                            # Rough estimation: £50K-£100K revenue per employee for IT services
                            if turnover > 0:
                                rev_per_employee = 75000  # Average for IT services
                                estimated_count = int(turnover / rev_per_employee)
                                
                                if estimated_count <= 10:
                                    rev_based_range = '1-10'
                                elif estimated_count <= 50:
                                    rev_based_range = '11-50'
                                elif estimated_count <= 200:
                                    rev_based_range = '51-200'
                                else:
                                    rev_based_range = '200+'
                                
                                # Use revenue-based estimate if it seems more reasonable
                                if not estimated_employees or (estimated_count >= 5 and estimated_count <= 500):
                                    estimated_employees = f"{estimated_count}"
                                    employee_range = rev_based_range
                        except:
                            pass
                    
                    # Set final employee estimates
                    accounts_info['employees'] = estimated_employees or base_estimate
                    accounts_info['employee_range'] = employee_range or base_estimate
                    accounts_info['employee_count'] = estimated_employees
                    
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
