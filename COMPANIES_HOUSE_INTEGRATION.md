# Companies House Integration - Enhanced

## Overview
The CCS Quote Tool now fetches comprehensive financial and director information from Companies House API to provide detailed business intelligence.

## Financial Data Captured

### Company Size & Revenue
- **Company Size Classification**: Micro-entity, Small, Medium, Large
- **Revenue Estimates**:
  - Micro-entity: £0 - £632K
  - Small: £632K - £10.2M
  - Medium: £10.2M - £36M
  - Large: £36M+

### Financial Metrics
1. **Shareholders' Funds** - Total equity value
2. **Cash at Bank** - Liquid assets/cash reserves
3. **Turnover/Revenue** - Annual sales
4. **Net Assets** - Total asset value
5. **Current Assets** - Short-term assets
6. **Current Liabilities** - Short-term debts
7. **Profit Before Tax** - Profitability indicator

### Company Information
- **Filing Date** - When last accounts were filed
- **Accounts Type** - Full/Abbreviated/Micro-entity
- **Period Dates** - Accounting period covered
- **Estimated Employees** - Based on number of officers

## Active Directors/Officers Information

### Data Captured for Each Director
1. **Name** - Full name (title case)
2. **Role** - Director, Secretary, LLP Member, etc.
3. **Appointed On** - Date of appointment
4. **Occupation** - Professional occupation
5. **Nationality** - Country of citizenship
6. **Country of Residence** - Where they reside
7. **Date of Birth** - Month/Year (for privacy)
8. **Service Address** - Business address
9. **Officer ID** - Unique Companies House ID

### Filtering
- **Active Only** - Automatically filters out resigned officers
- **Top 10 Limit** - Shows up to 10 most relevant officers
- **Current Status** - Only shows currently active appointments

## How It Works

### 1. Data Fetching Process
```
Customer Record → Companies House API
    ↓
Company Number Lookup
    ↓
Fetch Company Details
    ↓
Fetch Accounts Data
    ↓
Fetch Officers/Directors
    ↓
Extract Financial Metrics
    ↓
Format for AI Analysis
```

### 2. AI Analysis Integration
All Companies House data is passed to GPT-5 for intelligent analysis:

- **Financial Health Assessment**
- **Budget Capability Estimation**
- **Growth Potential Analysis**
- **Decision Maker Identification**
- **Company Stability Evaluation**
- **Technology Investment Capacity**

### 3. Use Cases

#### Sales Intelligence
- Identify key decision makers (directors)
- Assess financial capacity for IT projects
- Understand company size and structure
- Evaluate growth trajectory

#### Lead Scoring
- Company financial health
- Cash reserves for projects
- Recent profitability
- Number and experience of directors

#### Relationship Building
- Know who the directors are
- Understand their backgrounds
- See how long they've been with company
- Identify relevant experience

## API Endpoints Used

### Company Profile
```
GET /company/{company_number}
```

### Officers/Directors
```
GET /company/{company_number}/officers
```

### Filing History
```
GET /company/{company_number}/filing-history
```

## Data Privacy

### Compliant with UK Data Protection
- **Public Information Only** - All data is publicly available
- **No Personal Details** - Only business-relevant information
- **Date of Birth** - Month/Year only (not full DOB)
- **Addresses** - Service addresses only (business)
- **GDPR Compliant** - Using official public register

## Example Output

### Financial Summary
```
Company Size: Medium
Estimated Revenue: £10.2M - £36M
Shareholders' Funds: £2,500,000
Cash at Bank: £350,000
Turnover: £8,750,000
Net Assets: £3,200,000
Employees: 51-200
```

### Directors Example
```
Active Directors (3):

1. John Smith
   Role: Director
   Appointed: 2015-03-15
   Occupation: IT Consultant
   Nationality: British
   Residence: UK
   Age: Born 05/1978

2. Sarah Johnson
   Role: Director
   Appointed: 2018-06-20
   Occupation: Business Consultant
   Nationality: British
   Residence: UK
   Age: Born 11/1985

3. Michael Brown
   Role: Company Secretary
   Appointed: 2019-01-10
   Occupation: Accountant
   Nationality: British
   Residence: UK
   Age: Born 03/1972
```

## Benefits for Sales

### Better Qualification
- **Financial Capacity** - Know if they can afford projects
- **Decision Makers** - Direct contact with directors
- **Company Stability** - Assess long-term viability
- **Growth Indicators** - Spot expansion opportunities

### Personalized Approach
- **Director Background** - Tailor pitch to their experience
- **Company Maturity** - Adjust solution complexity
- **Financial Position** - Right-size the proposal
- **Industry Context** - Understand their sector

### Risk Management
- **Financial Health** - Spot payment risks
- **Company Status** - Ensure they're active
- **Director Changes** - Note recent appointments
- **Filing Compliance** - Check they file on time

## Configuration

### API Key Required
Set up Companies House API key in:
- **Admin → API Settings**
- **Service**: Companies House
- **Key Type**: REST API key (free)
- **Get Key**: https://developer.company-information.service.gov.uk/

### Automatic Updates
Data is fetched automatically when:
- Creating new customer/prospect
- Running AI analysis
- Viewing customer details
- Generating quotes

## Future Enhancements

### Planned Features
1. **Historical Analysis** - Track financial trends over time
2. **Significant Control** - PSC (People with Significant Control) data
3. **Charges** - Check for secured debts
4. **Insolvency** - Monitor for warning signs
5. **Multiple Directorships** - Cross-reference director networks
6. **Industry Benchmarking** - Compare to sector averages

Last Updated: 2025-10-07


