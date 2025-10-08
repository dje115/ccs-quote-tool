#!/usr/bin/env python3
"""
Script to run AI analysis and fetch updated financial data
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_ai_analysis():
    from app import app, db
    from utils.customer_intelligence import CustomerIntelligenceService
    from models_crm import Customer

    with app.app_context():
        # Find Kazzoo IT Solutions customer
        customer = Customer.query.filter(Customer.company_name.ilike('%kazzoo%')).first()
        
        if customer:
            print(f'Found customer: {customer.company_name} (ID: {customer.id})')
            print(f'Current status: {customer.status.value if customer.status else None}')
            print(f'Has Companies House data: {bool(customer.companies_house_data)}')
            
            # Run AI analysis to fetch updated financial data
            intelligence_service = CustomerIntelligenceService()
            print('Running AI analysis to fetch updated financial data...')
            
            result = intelligence_service.analyze_company(customer.id)
            
            if result.get('success'):
                print('AI analysis completed successfully!')
                
                # Check if we got new financial data
                customer = Customer.query.get(customer.id)  # Refresh from DB
                if customer.companies_house_data:
                    import json
                    ch_data = json.loads(customer.companies_house_data)
                    accounts = ch_data.get('accounts_detail', {})
                    
                    print(f'Updated financial data:')
                    print(f'  Shareholders Funds: {accounts.get("shareholders_funds")}')
                    print(f'  Cash at Bank: {accounts.get("cash_at_bank")}')
                    print(f'  Employee Count: {accounts.get("employee_count")}')
                    print(f'  Company Size: {accounts.get("company_size")}')
                    print(f'  Years of Data: {accounts.get("years_of_data")}')
                    
                    # Show detailed financials
                    detailed_financials = accounts.get('detailed_financials', [])
                    if detailed_financials:
                        print(f'  Detailed Financial History:')
                        for i, year_data in enumerate(detailed_financials[:2]):
                            filing_date = year_data.get('filing_date', 'Unknown')
                            shareholders_funds = year_data.get('shareholders_funds', 0)
                            cash_at_bank = year_data.get('cash_at_bank', 0)
                            employees = year_data.get('employees', 'N/A')
                            
                            print(f'    Year {i+1}: {filing_date}')
                            print(f'      Shareholders Funds: £{shareholders_funds:,.0f}')
                            print(f'      Cash at Bank: £{cash_at_bank:,.0f}')
                            print(f'      Employees: {employees}')
                else:
                    print('No Companies House data found after analysis')
            else:
                print(f'AI analysis failed: {result.get("error")}')
        else:
            print('Kazzoo IT Solutions customer not found')

if __name__ == "__main__":
    run_ai_analysis()
