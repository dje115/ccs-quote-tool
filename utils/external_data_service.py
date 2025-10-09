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
            # Try to detect which ix namespace is used (2008 or 2013)
            ix_namespace = 'http://www.xbrl.org/2008/inlineXBRL'  # Most common in UK accounts
            if 'http://www.xbrl.org/2013/inlineXBRL' in content:
                ix_namespace = 'http://www.xbrl.org/2013/inlineXBRL'
            
            namespaces = {
                'ix': ix_namespace,
                'xbrli': 'http://www.xbrl.org/2003/instance',
                'core': 'http://xbrl.frc.org.uk/fr/2023-01-01/core',
                'e': 'http://xbrl.frc.org.uk/fr/2023-01-01/core',  # Alternative namespace prefix
                'bus': 'http://xbrl.frc.org.uk/cd/2023-01-01/business',
                'b': 'http://xbrl.frc.org.uk/FRS-102/2023-01-01',
                'd': 'http://xbrl.frc.org.uk/cd/2023-01-01/business'
            }
            
            # Extract financial data using XBRL tags
            # Try multiple namespace prefixes and tag variations
            tag_variations = [
                # Net Assets / Shareholders' Funds
                ('net_assets', ['e:NetAssetsLiabilities', 'core:NetAssetsLiabilities', 'e:NetAssets', 'core:NetAssets', 'e:Equity', 'core:Equity']),
                # Cash at Bank
                ('cash_at_bank', ['e:CashBankOnHand', 'core:CashBankOnHand', 'e:CashAtBank', 'core:CashAtBank', 'e:CashBankInHand', 'core:CashBankInHand']),
                # Total Equity
                ('total_equity', ['e:Equity', 'core:Equity', 'e:TotalEquity', 'core:TotalEquity', 'e:ShareholderFunds', 'core:ShareholderFunds']),
                # Property, Plant & Equipment
                ('ppe', ['e:PropertyPlantEquipment', 'core:PropertyPlantEquipment', 'e:PPE', 'core:PPE', 'e:TangibleFixedAssets', 'core:TangibleFixedAssets']),
                # Trade Debtors
                ('trade_debtors', ['e:TradeDebtorsTradeReceivables', 'core:TradeDebtorsTradeReceivables', 'e:TradeDebtors', 'core:TradeDebtors', 'e:Debtors', 'core:Debtors']),
                # Turnover/Revenue
                ('turnover', ['e:TurnoverRevenue', 'core:TurnoverRevenue', 'e:Revenue', 'core:Revenue', 'e:Turnover', 'core:Turnover']),
                # Profit Before Tax
                ('profit_before_tax', ['e:ProfitLossOnOrdinaryActivitiesBeforeTax', 'core:ProfitLossOnOrdinaryActivitiesBeforeTax', 'e:ProfitBeforeTax', 'core:ProfitBeforeTax', 'e:ProfitLossBeforeTax', 'core:ProfitLossBeforeTax']),
                # Operating Profit
                ('operating_profit', ['e:OperatingProfitLoss', 'core:OperatingProfitLoss', 'e:OperatingProfit', 'core:OperatingProfit', 'e:ProfitLossFromOperations', 'core:ProfitLossFromOperations']),
                # Gross Profit
                ('gross_profit', ['e:GrossProfitLoss', 'core:GrossProfitLoss', 'e:GrossProfit', 'core:GrossProfit']),
                # Cost of Sales
                ('cost_of_sales', ['e:CostSales', 'core:CostSales', 'e:CostOfSales', 'core:CostOfSales']),
                # Administrative Expenses
                ('admin_expenses', ['e:AdministrativeExpenses', 'core:AdministrativeExpenses', 'e:AdminExpenses', 'core:AdminExpenses'])
            ]
            
            for field_name, tag_list in tag_variations:
                for tag in tag_list:
                    elements = root.findall(f'.//ix:nonFraction[@name="{tag}"]', namespaces)
                    if elements:
                        # Get the most recent year's data (usually the first one)
                        for elem in elements[:1]:
                            try:
                                value = float(elem.text.replace(',', ''))
                                financial_data[field_name] = value
                                break
                            except:
                                continue
                        if field_name in financial_data:
                            break  # Found the data, move to next field
            # Extract employee count
            employee_tag_variations = [
                'e:AverageNumberEmployeesDuringPeriod',
                'core:AverageNumberEmployeesDuringPeriod',
                'e:NumberOfEmployees',
                'core:NumberOfEmployees',
                'e:Employees',
                'core:Employees',
                'bus:AverageNumberEmployees',
                'd:AverageNumberEmployees'
            ]
            
            for tag in employee_tag_variations:
                elements = root.findall(f'.//ix:nonFraction[@name="{tag}"]', namespaces)
                if elements:
                    for elem in elements[:1]:
                        try:
                            value = int(float(elem.text))
                            financial_data['employees'] = value
                            break
                        except:
                            continue
                    if 'employees' in financial_data:
                        break
            
            # Extract financial year periods from context elements
            # Period dates are stored in xbrli:context elements
            try:
                contexts = root.findall('.//xbrli:context', namespaces)
                for context in contexts:
                    context_id = context.get('id', '')
                    # Look for contexts that represent the current period
                    if 'current' in context_id.lower() or 'period' in context_id.lower():
                        period = context.find('.//xbrli:period', namespaces)
                        if period is not None:
                            start_date = period.find('.//xbrli:startDate', namespaces)
                            end_date = period.find('.//xbrli:endDate', namespaces)
                            instant = period.find('.//xbrli:instant', namespaces)
                            
                            if start_date is not None and start_date.text:
                                financial_data['period_start'] = start_date.text.strip()
                            if end_date is not None and end_date.text:
                                financial_data['period_end'] = end_date.text.strip()
                            if instant is not None and instant.text:
                                financial_data['reporting_date'] = instant.text.strip()
                            
                            # If we found period_end, that's our most important date
                            if 'period_end' in financial_data:
                                break
            except:
                pass
            
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
                                        # Extract document ID from the metadata URL
                                        # URL format: https://document-api.company-information.service.gov.uk/document/{document_id}
                                        document_id = document_metadata_url.split('/')[-1]
                                        print(f"[IXBRL] Document ID: {document_id}")
                                        
                                        # Step 1: Get document metadata using the correct Document API endpoint
                                        # Document API uses different authentication - extract API key from Authorization header
                                        auth_header = headers.get('Authorization', '')
                                        if auth_header.startswith('Basic '):
                                            api_key = auth_header.replace('Basic ', '')
                                            doc_headers = {'api_key': api_key}
                                        else:
                                            doc_headers = headers.copy()
                                        
                                        metadata_url = f"https://document-api.company-information.service.gov.uk/document/{document_id}"
                                        metadata_response = self.session.get(metadata_url, headers=doc_headers, timeout=10)
                                        
                                        if metadata_response.status_code == 200:
                                            metadata = metadata_response.json()
                                            print(f"[IXBRL] Document metadata: {list(metadata.keys())}")
                                            
                                            # Check available content types
                                            resources = metadata.get('resources', {})
                                            available_types = list(resources.keys())
                                            print(f"[IXBRL] Available content types: {available_types}")
                                            
                                            # Look for iXBRL/XHTML format
                                            target_content_type = None
                                            for content_type in ['application/xhtml+xml', 'application/xml', 'text/html']:
                                                if content_type in available_types:
                                                    target_content_type = content_type
                                                    break
                                            
                                            if target_content_type:
                                                print(f"[IXBRL] Using content type: {target_content_type}")
                                                
                                                # Step 2: Download the document using the correct endpoint
                                                content_url = f"https://document-api.company-information.service.gov.uk/document/{document_id}/content"
                                                content_headers = doc_headers.copy()
                                                content_headers['Accept'] = target_content_type
                                                
                                                content_response = self.session.get(content_url, headers=content_headers, timeout=30, allow_redirects=True)
                                                
                                                if content_response.status_code == 200:
                                                    content = content_response.text
                                                    print(f"[IXBRL] Downloaded iXBRL document for {company_number}, size: {len(content)} chars")
                                                    
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
                                                        
                                                        if 'turnover' in financial_data:
                                                            year_data['turnover'] = financial_data['turnover']
                                                            if i == 0:
                                                                accounts_info['turnover_current'] = financial_data['turnover']
                                                                accounts_info['turnover'] = f"£{financial_data['turnover']:,.0f}"
                                                            elif i == 1:
                                                                accounts_info['turnover_previous'] = financial_data['turnover']
                                                        
                                                        if 'profit_before_tax' in financial_data:
                                                            year_data['profit_before_tax'] = financial_data['profit_before_tax']
                                                        
                                                        if 'employees' in financial_data:
                                                            year_data['employees'] = financial_data['employees']
                                                            if i == 0:
                                                                accounts_info['employee_count'] = financial_data['employees']
                                                        
                                                        # Map period information
                                                        if 'period_start' in financial_data:
                                                            year_data['period_start'] = financial_data['period_start']
                                                        if 'period_end' in financial_data:
                                                            year_data['period_end'] = financial_data['period_end']
                                                        if 'reporting_date' in financial_data:
                                                            year_data['reporting_date'] = financial_data['reporting_date']
                                                        
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
                                                else:
                                                    print(f"[IXBRL] Error downloading document content: {content_response.status_code}")
                                            else:
                                                print(f"[IXBRL] No suitable content type found. Available: {available_types}")
                                        else:
                                            print(f"[IXBRL] Metadata request failed: {metadata_response.status_code}")
                                            print(f"[IXBRL] Error: {metadata_response.text[:200]}")
                                    except Exception as meta_e:
                                        print(f"Error accessing iXBRL document: {meta_e}")
                            
                            # Fallback: Try direct Companies House web URL if Document API fails
                            if not any([year_data.get('shareholders_funds'), year_data.get('cash_at_bank')]):
                                transaction_id = filing.get('transaction_id')
                                if transaction_id:
                                    # Try the direct Companies House web URL for iXBRL documents
                                    direct_ixbrl_url = f"https://find-and-update.company-information.service.gov.uk/company/{company_number}/filing-history/{transaction_id}/document?format=xhtml&download=1"
                                    print(f"[IXBRL] Trying direct web URL: {direct_ixbrl_url}")
                                    
                                    try:
                                        # Use a different session for web scraping (no auth required for public URLs)
                                        web_session = requests.Session()
                                        web_session.headers.update({
                                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                                        })
                                        
                                        direct_response = web_session.get(direct_ixbrl_url, timeout=30)
                                        if direct_response.status_code == 200:
                                            content = direct_response.text
                                            print(f"[IXBRL] Successfully downloaded iXBRL document via web URL, size: {len(content)} chars")
                                            
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
                                                
                                                if 'turnover' in financial_data:
                                                    year_data['turnover'] = financial_data['turnover']
                                                    if i == 0:
                                                        accounts_info['turnover_current'] = financial_data['turnover']
                                                        accounts_info['turnover'] = f"£{financial_data['turnover']:,.0f}"
                                                    elif i == 1:
                                                        accounts_info['turnover_previous'] = financial_data['turnover']
                                                
                                                if 'profit_before_tax' in financial_data:
                                                    year_data['profit_before_tax'] = financial_data['profit_before_tax']
                                                
                                                if 'employees' in financial_data:
                                                    year_data['employees'] = financial_data['employees']
                                                    if i == 0:
                                                        accounts_info['employee_count'] = financial_data['employees']
                                                
                                                # Map period information
                                                if 'period_start' in financial_data:
                                                    year_data['period_start'] = financial_data['period_start']
                                                if 'period_end' in financial_data:
                                                    year_data['period_end'] = financial_data['period_end']
                                                if 'reporting_date' in financial_data:
                                                    year_data['reporting_date'] = financial_data['reporting_date']
                                                
                                                if 'total_equity' in financial_data:
                                                    year_data['total_equity'] = financial_data['total_equity']
                                                
                                                if 'employees' in financial_data:
                                                    year_data['employees'] = financial_data['employees']
                                                    if i == 0:
                                                        accounts_info['employee_count'] = financial_data['employees']
                                                
                                                if 'trade_debtors' in financial_data:
                                                    year_data['trade_debtors'] = financial_data['trade_debtors']
                                                
                                                print(f"[IXBRL] Successfully extracted financial data via web URL: {financial_data}")
                                            else:
                                                print(f"[IXBRL] No financial data extracted from web URL document")
                                        else:
                                            print(f"[IXBRL] Direct web URL failed: {direct_response.status_code}")
                                    except Exception as web_e:
                                        print(f"[IXBRL] Error accessing direct web URL: {web_e}")
                                
                                # Final fallback: Try to extract from filing description
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
                    
                    # Fix year display - calculate financial year from filing date
                    for year_data in financial_history:
                        # Calculate financial year from period_end if available, otherwise from filing date
                        financial_year = None
                        
                        # First, try to get the period_end from the iXBRL document
                        if year_data.get('period_end'):
                            try:
                                from datetime import datetime
                                period_end = year_data['period_end']
                                # Handle various date formats
                                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                                    try:
                                        period_dt = datetime.strptime(period_end, fmt)
                                        financial_year = period_dt.year
                                        year_data['financial_year_end'] = period_end
                                        break
                                    except:
                                        continue
                            except:
                                pass
                        
                        # Fallback: Calculate from filing date
                        if not financial_year:
                            filing_date = year_data.get('filing_date')
                            if filing_date:
                                try:
                                    from datetime import datetime
                                    filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
                                    filing_year = filing_dt.year
                                    filing_month = filing_dt.month
                                    
                                    # UK companies typically file accounts 9 months after financial year end
                                    # Most companies have Dec 31 year-end, so:
                                    # - Filed Sep 2025 = 2024 financial year (filed 9 months after Dec 2024)
                                    # - Filed Jul 2024 = 2023 financial year (filed 7 months after Dec 2023)
                                    # - Filed Jun 2021 = 2020 financial year (filed 6 months after Dec 2020)
                                    
                                    # For this company, all filings appear to be previous year's accounts
                                    financial_year = filing_year - 1
                                    
                                    # Set the financial year end date
                                    year_data['financial_year_end'] = f"{financial_year}-12-31"
                                except:
                                    pass
                        
                        if financial_year:
                            year_data['financial_year'] = str(financial_year)
                    
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
                    
                    # Set final employee estimates - only if we don't have iXBRL data
                    if not accounts_info.get('employee_count'):
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
                'key_phrases': None,
                'locations': None,
                'additional_sites': None,
                'addresses': None
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
                        
                        # Extract location and address information
                        locations, addresses, additional_sites = self._extract_location_info(soup, text_content)
                        web_data['locations'] = locations
                        web_data['addresses'] = addresses
                        web_data['additional_sites'] = additional_sites
                        
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
                'website': self.get_web_company_data(company_name, website),
                'google_maps': self.get_google_maps_data(company_name, website)
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
    
    def _extract_location_info(self, soup, text_content: str) -> tuple:
        """Extract location, address, and additional site information from website"""
        locations = []
        addresses = []
        additional_sites = []
        
        try:
            # Extract addresses using regex patterns
            # UK postcode pattern
            postcode_pattern = r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b'
            postcodes = re.findall(postcode_pattern, text_content, re.IGNORECASE)
            addresses.extend(postcodes)
            
            # Look for address-like patterns
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(?:Street|Road|Avenue|Lane|Close|Drive|Way|Place|Court|Grove|Hill|Park|Gardens?|Square|Terrace|Crescent|Mews|Manor|House|Building|Centre|Center|Business Park|Industrial Estate|Trading Estate)\b',
                r'\b[A-Za-z\s]+(?:Street|Road|Avenue|Lane|Close|Drive|Way|Place|Court|Grove|Hill|Park|Gardens?|Square|Terrace|Crescent|Mews|Manor|House|Building|Centre|Center|Business Park|Industrial Estate|Trading Estate)\b'
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    # Clean up the match and add if it looks like a real address
                    cleaned = re.sub(r'\s+', ' ', match.strip())
                    if len(cleaned) > 10 and len(cleaned) < 100:  # Reasonable address length
                        addresses.append(cleaned)
            
            # Look for location mentions in specific contexts
            location_contexts = [
                r'office[s]?\s+in\s+([A-Za-z\s,]+)',
                r'located\s+in\s+([A-Za-z\s,]+)',
                r'based\s+in\s+([A-Za-z\s,]+)',
                r'serving\s+([A-Za-z\s,]+)',
                r'covering\s+([A-Za-z\s,]+)',
                r'operating\s+in\s+([A-Za-z\s,]+)'
            ]
            
            for pattern in location_contexts:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    cleaned = re.sub(r'\s+', ' ', match.strip())
                    if len(cleaned) > 2 and len(cleaned) < 50:
                        locations.append(cleaned)
            
            # Look for "Our Locations", "Contact Us", "Find Us" sections
            location_sections = soup.find_all(['div', 'section', 'p'], string=re.compile(r'(?:our\s+)?locations?|contact\s+us|find\s+us|visit\s+us|office[s]?|address[es]?', re.IGNORECASE))
            for section in location_sections:
                # Look for addresses in nearby elements
                parent = section.parent if section.parent else section
                for elem in parent.find_all(['p', 'div', 'span', 'li', 'td']):
                    text = elem.get_text().strip()
                    if any(keyword in text.lower() for keyword in ['street', 'road', 'avenue', 'lane', 'close', 'drive', 'way', 'place', 'point', 'barn', 'farm', 'industrial', 'estate']):
                        addresses.append(text)
            
            # Look for structured location data in tables or lists
            for table in soup.find_all(['table', 'ul', 'ol']):
                for row in table.find_all(['tr', 'li']):
                    row_text = row.get_text().strip()
                    if any(keyword in row_text.lower() for keyword in ['office', 'location', 'address', 'site']):
                        # Extract addresses from this row
                        for elem in row.find_all(['td', 'span', 'p', 'div']):
                            elem_text = elem.get_text().strip()
                            if any(keyword in elem_text.lower() for keyword in ['street', 'road', 'avenue', 'lane', 'close', 'drive', 'way', 'place', 'point', 'barn', 'farm', 'industrial', 'estate']):
                                addresses.append(elem_text)
            
            # Look for location information in navigation menus
            for nav in soup.find_all(['nav', 'ul']):
                for link in nav.find_all('a'):
                    link_text = link.get_text().strip().lower()
                    if any(keyword in link_text for keyword in ['location', 'office', 'contact', 'address', 'site']):
                        # Check if the link leads to a page with address info
                        href = link.get('href', '')
                        if href and ('contact' in href.lower() or 'location' in href.lower() or 'office' in href.lower()):
                            # This could be a location page
                            pass
            
            # Look for multiple office/site mentions
            site_patterns = [
                r'(?:office|site|location|branch|depot|facility|premises)\s+(?:in|at)\s+([A-Za-z\s,]+)',
                r'(?:our|the)\s+(?:office|site|location|branch|depot|facility|premises)\s+in\s+([A-Za-z\s,]+)',
                r'([A-Za-z\s]+)\s+(?:office|site|location|branch|depot|facility|premises)'
            ]
            
            for pattern in site_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    cleaned = re.sub(r'\s+', ' ', match.strip())
                    if len(cleaned) > 2 and len(cleaned) < 50:
                        additional_sites.append(cleaned)
            
            # Remove duplicates and clean up
            addresses = list(set([addr.strip() for addr in addresses if addr.strip()]))
            locations = list(set([loc.strip() for loc in locations if loc.strip()]))
            additional_sites = list(set([site.strip() for site in additional_sites if site.strip()]))
            
        except Exception as e:
            print(f"Error extracting location info: {e}")
        
        return locations[:10], addresses[:10], additional_sites[:10]
    
    def _is_company_name_match(self, company_name: str, location_name: str) -> bool:
        """
        Check if a location name is a good match for the company name
        """
        if not company_name or not location_name:
            return False
        
        # Convert both to lowercase for case-insensitive comparison
        company_lower = company_name.lower().strip()
        location_lower = location_name.lower().strip()
        
        # Exact match
        if company_lower == location_lower:
            return True
        
        # Check if location name contains the full company name
        if company_lower in location_lower:
            return True
        
        # Check if company name contains the location name (for partial matches)
        if location_lower in company_lower:
            return True
        
        # Remove common suffixes and check again
        suffixes = [' ltd', ' limited', ' plc', ' llc', ' inc', ' corp', ' company', ' co']
        clean_company = company_lower
        clean_location = location_lower
        
        for suffix in suffixes:
            clean_company = clean_company.replace(suffix, '').strip()
            clean_location = clean_location.replace(suffix, '').strip()
        
        # Check cleaned names
        if clean_company == clean_location:
            return True
        if clean_company in clean_location:
            return True
        if clean_location in clean_company:
            return True
        
        return False
    
    def _has_significant_word_match(self, company_name: str, location_name: str) -> bool:
        """
        Check if location has significant word overlap with company name
        """
        if not company_name or not location_name:
            return False
        
        # Convert to lowercase for case-insensitive comparison
        company_lower = company_name.lower().strip()
        location_lower = location_name.lower().strip()
        
        # Split into words and remove common words
        common_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'ltd', 'limited', 'plc', 'llc', 'inc', 'corp', 'company', 'co'}
        
        company_words = set(word.strip() for word in company_lower.split() if word.strip().lower() not in common_words and len(word.strip()) > 2)
        location_words = set(word.strip() for word in location_lower.split() if word.strip().lower() not in common_words and len(word.strip()) > 2)
        
        # Must have at least 50% word overlap for significant words
        if company_words and location_words:
            overlap = company_words.intersection(location_words)
            overlap_ratio = len(overlap) / max(len(company_words), len(location_words))
            return overlap_ratio >= 0.5
        
        return False
    
    def get_google_maps_data(self, company_name: str, website: str = None) -> Dict[str, Any]:
        """
        Get company location data from Google Maps Places API v1
        """
        try:
            # Get Google Maps API key from settings
            google_api_key = self._get_api_key('google_maps')
            
            if not google_api_key:
                return {
                    'success': False,
                    'error': 'Google Maps API key not configured',
                    'data': {}
                }
            
            maps_data = {
                'locations': [],
                'addresses': [],
                'phone_numbers': [],
                'business_hours': [],
                'ratings': [],
                'place_id': None,
                'additional_locations': []
            }
            
            # Search for company locations using Google Places API v1
            # Start with exact company name search
            search_queries = [company_name]
            
            # Add comprehensive search variations to find all locations
            if ' ' in company_name:  # Only add variations for multi-word company names
                variations = [
                    f'"{company_name}"',  # Exact phrase search
                    f"{company_name} UK",  # Add UK for better UK-specific results
                    f"{company_name} office",  # Find office locations
                    f"{company_name} branch",  # Find branch locations
                    f"{company_name} location"  # Find location mentions
                ]
                search_queries.extend(variations)
            
            # Add UK region and county-based searches for comprehensive coverage
            uk_searches = [
                # England Regions (broad coverage)
                f"{company_name} South East England",
                f"{company_name} South West England", 
                f"{company_name} London",
                f"{company_name} East Midlands",
                f"{company_name} West Midlands",
                f"{company_name} Yorkshire",
                f"{company_name} North West England",
                f"{company_name} North East England",
                f"{company_name} East of England",
                # Scotland
                f"{company_name} Scotland",
                f"{company_name} Central Scotland",
                f"{company_name} Highlands Scotland",
                # Wales
                f"{company_name} Wales",
                f"{company_name} South Wales",
                f"{company_name} North Wales",
                # Northern Ireland
                f"{company_name} Northern Ireland",
                f"{company_name} Belfast",
                # Major UK Counties (for specific towns like Wimborne)
                f"{company_name} Dorset",           # Wimborne, Bournemouth, Poole
                f"{company_name} Hampshire",        # Southampton, Portsmouth
                f"{company_name} Kent",             # Canterbury, Maidstone
                f"{company_name} Surrey",           # Guildford, Woking
                f"{company_name} Sussex",           # Brighton, Hastings
                f"{company_name} Berkshire",        # Reading, Windsor
                f"{company_name} Oxfordshire",      # Oxford, Banbury
                f"{company_name} Buckinghamshire",  # Milton Keynes, Aylesbury
                f"{company_name} Essex",            # Chelmsford, Colchester
                f"{company_name} Hertfordshire",    # St Albans, Watford
                f"{company_name} Cambridgeshire",   # Cambridge, Peterborough
                f"{company_name} Norfolk",          # Norwich, King's Lynn
                f"{company_name} Suffolk",          # Ipswich, Bury St Edmunds
                f"{company_name} Leicestershire",   # Leicester, Loughborough
                f"{company_name} Derbyshire",       # Derby, Chesterfield
                f"{company_name} Nottinghamshire",  # Nottingham, Mansfield
                f"{company_name} Staffordshire",    # Stoke, Stafford
                f"{company_name} Warwickshire",     # Coventry, Warwick
                f"{company_name} Worcestershire",   # Worcester, Kidderminster
                f"{company_name} West Yorkshire",   # Leeds, Bradford
                f"{company_name} South Yorkshire",  # Sheffield, Rotherham
                f"{company_name} North Yorkshire",  # York, Harrogate
                f"{company_name} Lancashire",       # Preston, Blackpool
                f"{company_name} Greater Manchester", # Manchester, Bolton
                f"{company_name} Merseyside",       # Liverpool, Wirral
                f"{company_name} Tyne and Wear",    # Newcastle, Sunderland
                f"{company_name} Durham",           # Durham, Darlington
                f"{company_name} Northumberland",   # Northumberland
                # Scotland Counties
                f"{company_name} Edinburgh",        # Edinburgh
                f"{company_name} Glasgow",          # Glasgow
                f"{company_name} Aberdeen",         # Aberdeen
                f"{company_name} Dundee",           # Dundee
                # Wales Counties
                f"{company_name} Cardiff",          # Cardiff
                f"{company_name} Swansea",          # Swansea
                f"{company_name} Newport",          # Newport
            ]
            search_queries.extend(uk_searches)
            
            all_locations = []
            
            print(f"[GOOGLE MAPS] Searching for '{company_name}' with {len(search_queries)} queries")
            
            for query in search_queries:
                # Use Google Places API v1 Text Search
                search_url = "https://places.googleapis.com/v1/places:searchText"
                headers = {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': google_api_key,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.primaryType'
                }
                
                payload = {
                    'textQuery': query
                }
                
                response = self.session.post(search_url, headers=headers, json=payload, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('places'):
                        place_ids = [place['id'] for place in data['places']]
                        print(f"[GOOGLE MAPS] Query '{query}' found {len(place_ids)} places")
                        
                        # Get detailed information for each place
                        for place_id in place_ids:
                            details = self._get_google_place_details_v1(place_id, google_api_key)
                            if details:
                                all_locations.append(details)
                    else:
                        print(f"[GOOGLE MAPS] Query '{query}' found no places")
            
            # Filter and de-duplicate locations
            unique_locations = {}
            company_name_lower = company_name.lower().strip()
            
            print(f"[GOOGLE MAPS] Total locations found: {len(all_locations)}")
            
            for location in all_locations:
                location_name = location.get('name', '').lower().strip()
                address_key = (location.get('address') or '').lower().strip()
                
                print(f"[GOOGLE MAPS] Checking: '{location_name}' at '{address_key}'")
                
                # Only include locations that actually match the company name
                if self._is_company_name_match(company_name_lower, location_name):
                    if address_key and address_key not in unique_locations:
                        unique_locations[address_key] = location
                        print(f"[GOOGLE MAPS] ✓ MATCH: Added '{location_name}'")
                    else:
                        print(f"[GOOGLE MAPS] ✗ DUPLICATE: Skipped '{location_name}' (duplicate address)")
                else:
                    print(f"[GOOGLE MAPS] ✗ NO MATCH: Rejected '{location_name}'")
            
            print(f"[GOOGLE MAPS] Strict filtering result: {len(unique_locations)} locations")
            
            # If no matches found with strict filtering, try more lenient matching
            if not unique_locations:
                print(f"[GOOGLE MAPS] Trying lenient matching...")
                for location in all_locations:
                    location_name = location.get('name', '').lower().strip()
                    address_key = (location.get('address') or '').lower().strip()
                    
                    # More lenient matching - check if any significant words match
                    if self._has_significant_word_match(company_name_lower, location_name):
                        if address_key and address_key not in unique_locations:
                            unique_locations[address_key] = location
                            print(f"[GOOGLE MAPS] ✓ LENIENT MATCH: Added '{location_name}'")
                        else:
                            print(f"[GOOGLE MAPS] ✗ LENIENT DUPLICATE: Skipped '{location_name}'")
                    else:
                        print(f"[GOOGLE MAPS] ✗ LENIENT NO MATCH: Rejected '{location_name}'")
            
            print(f"[GOOGLE MAPS] Final result: {len(unique_locations)} unique locations")
            
            
            # Convert back to list and populate maps_data
            maps_data['locations'] = list(unique_locations.values())
            
            # Extract addresses and other data
            for location in maps_data['locations']:
                if location.get('address'):
                    maps_data['addresses'].append(location['address'])
                if location.get('phone'):
                    maps_data['phone_numbers'].append(location['phone'])
                if location.get('rating'):
                    maps_data['ratings'].append(location['rating'])
            
            return {
                'success': True,
                'data': maps_data,
                'source': 'google_maps_api_v1'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Google Maps API error: {str(e)}',
                'data': {}
            }
    
    def _search_google_places(self, query: str, api_key: str) -> List[Dict]:
        """Search Google Places with a specific query"""
        try:
            places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                'query': query,
                'key': api_key,
                'fields': 'place_id,name,formatted_address,geometry,types,rating,formatted_phone_number'
            }
            
            response = self.session.get(places_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK' and data.get('results'):
                    return [{
                        'name': place.get('name', ''),
                        'address': place.get('formatted_address', ''),
                        'phone': place.get('formatted_phone_number', ''),
                        'rating': place.get('rating', 0),
                        'place_id': place.get('place_id', '')
                    } for place in data['results']]
            
            return []
            
        except Exception as e:
            print(f"Error searching Google Places: {e}")
            return []
    
    def _get_google_place_details_v1(self, place_id: str, api_key: str) -> Dict:
        """Get detailed information about a specific place using Places API v1"""
        try:
            details_url = f"https://places.googleapis.com/v1/places/{place_id}"
            headers = {
                'X-Goog-Api-Key': api_key
            }
            params = {
                'fields': 'id,displayName,formattedAddress,addressComponents,location,internationalPhoneNumber,websiteUri,rating,userRatingCount,primaryType'
            }
            
            response = self.session.get(details_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Convert v1 response to our expected format
                return {
                    'name': data.get('displayName', {}).get('text', ''),
                    'address': data.get('formattedAddress', ''),
                    'phone': data.get('internationalPhoneNumber', ''),
                    'website': data.get('websiteUri', ''),
                    'rating': data.get('rating', 0),
                    'location': data.get('location', {}),
                    'place_id': data.get('id', ''),
                    'type': data.get('primaryType', '')
                }
            
            return {}
            
        except Exception as e:
            print(f"Error getting place details: {e}")
            return {}
