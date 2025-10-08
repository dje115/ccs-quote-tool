# CCS Quote Tool - Version 1.1

A comprehensive lead generation and customer relationship management (CRM) system powered by GPT-5 AI, designed for IT service providers and cabling companies.

## 🆕 What's New in v1.1.0

### Enhanced Location Discovery
- **Google Maps Places API v1 Integration**: Automatically discovers multiple office locations for businesses
- **Comprehensive Address Analysis**: Finds all business locations including branches, offices, and facilities
- **Enhanced Location Display**: Shows Google Maps data with ratings, phone numbers, and complete addresses
- **Improved AI Location Analysis**: AI now uses Google Maps data for more accurate location intelligence

### Financial Data Enhancements
- **iXBRL Document Parsing**: Direct parsing of Companies House financial documents
- **Multi-year Financial Analysis**: Historical financial data extraction and trend analysis
- **Enhanced Employee Estimation**: More accurate employee count from financial filings
- **Financial Year Calculation**: Proper financial year display (filing year - 1)

### Lead Generation Improvements
- **Background Processing**: Campaigns run in separate processes to survive Flask reloads
- **Enhanced Competitor Analysis**: AI identifies competitors and creates dedicated campaigns
- **Improved Deduplication**: Better duplicate detection across all campaigns
- **Visual Lead Indicators**: Highlights leads without verified websites

### UI/UX Enhancements
- **View All Leads**: Comprehensive lead overview across all campaigns
- **Enhanced Customer Detail Views**: Better display of financial and location data
- **Improved Navigation**: Added "View Leads" buttons throughout the interface
- **Financial Analysis Modals**: Detailed financial data display with multi-year history

## 🚀 Features

### Lead Generation
- **AI-Powered Lead Discovery**: Uses GPT-5 with web search to find potential customers
- **Geographic Targeting**: Search by postcode and radius for localized leads
- **Business Type Filtering**: Focus on IT/MSP companies, cabling services, and related businesses
- **Real-time Campaign Processing**: Background processing ensures smooth user experience
- **Companies House Integration**: Automatic company data enrichment
- **LinkedIn Data Extraction**: Professional network information gathering
- **Google Maps Location Discovery**: Automatic discovery of all business locations

### Customer Management (CRM)
- **Lead to Customer Conversion**: Seamless conversion with data preservation
- **Contact Management**: Multiple contacts per customer with role-based organization
- **Business Intelligence**: AI-generated company analysis and opportunity assessment
- **Interaction Tracking**: Complete history of customer communications
- **Quote Management**: Integrated quoting system for proposals
- **Enhanced Location Analysis**: Google Maps integration for comprehensive address data

### AI Analysis
- **Company Profiling**: Automated business intelligence generation
- **Technology Needs Assessment**: AI-predicted IT requirements
- **Competitor Analysis**: Market positioning insights and competitor campaign creation
- **Opportunity Scoring**: Lead qualification and prioritization
- **Risk Assessment**: Business viability evaluation
- **Financial Health Analysis**: Multi-year financial trend analysis and health scoring
- **Location Intelligence**: Comprehensive address and site analysis

## 🛠️ Technology Stack

- **Backend**: Flask (Python 3.13)
- **Database**: SQLite with SQLAlchemy ORM
- **AI Engine**: OpenAI GPT-5 and GPT-5-mini with web search capabilities
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap 5)
- **External APIs**: 
  - OpenAI API (GPT-5/GPT-5-mini)
  - Companies House API
  - Google Maps Places API v1
  - LinkedIn API integration

## 📋 Requirements

### System Requirements
- Python 3.11+
- Windows 10/11 (tested)
- 4GB RAM minimum
- Internet connection for AI and external APIs

### Python Dependencies
```
Flask>=2.3.0
Flask-SQLAlchemy>=3.0.0
Flask-Login>=0.6.0
openai>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

## 🚀 Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/dje115/ccs-quote-tool.git
cd ccs-quote-tool
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure API keys** in the database settings:
   - OpenAI API key (for GPT-5)
   - Companies House API key
   - Google Maps Places API key

4. **Run the application**:
```bash
python app.py
```

5. **Access the application** at `http://localhost:5000`

## 📖 Usage Guide

### Lead Generation Workflow

1. **Create a Campaign**:
   - Navigate to Lead Generation → New Campaign
   - Define search parameters (postcode, radius, business types)
   - Set campaign name and description

2. **Run AI Analysis**:
   - Campaign runs in background using GPT-5 with web search
   - AI discovers leads, analyzes websites, and enriches data
   - Google Maps integration finds all business locations

3. **Review and Qualify**:
   - View generated leads with AI analysis
   - Review business intelligence and location data
   - Qualify leads based on AI scoring

4. **Convert to Customers**:
   - Convert qualified leads to customers
   - Preserve all AI analysis and external data
   - Begin CRM workflow

### Customer Management

1. **Customer Profiles**:
   - Comprehensive business intelligence
   - Financial data from Companies House
   - Google Maps location data
   - Contact management

2. **AI Analysis**:
   - Technology needs assessment
   - Competitor identification
   - Opportunity scoring
   - Risk analysis

3. **Quote Generation**:
   - AI-powered quote creation
   - Product recommendations
   - Cost estimation

## 🔧 Configuration

### API Keys Setup

The system requires the following API keys:

1. **OpenAI API Key**:
   - Required for AI analysis and lead generation
   - Supports GPT-5 and GPT-5-mini models

2. **Companies House API Key**:
   - Required for UK company data and financial information
   - Register at: https://developer.company-information.service.gov.uk/

3. **Google Maps Places API Key**:
   - Required for location discovery and verification
   - Enable Places API in Google Cloud Console

### Database Configuration

The system uses SQLite by default. Database file: `instance/app.db`

## 📊 Database Schema

### Core Entities

- **Users**: Authentication and access control
- **Customers**: Company information and business intelligence
- **Contacts**: Individual contacts within companies
- **LeadGenerationCampaigns**: AI-powered lead discovery campaigns
- **Leads**: Prospects identified through campaigns
- **Quotes**: Project quotes and estimates

### Key Features

- **Lead Scoring**: 0-100 scale for lead qualification
- **Business Sector Classification**: Automated sector identification
- **Financial Data Storage**: Companies House financial information
- **Location Data**: Google Maps integration for address verification
- **AI Analysis Storage**: Complete AI analysis as JSON

## 🔍 Recent Improvements (v1.1.0)

### Technical Enhancements
- Fixed Unicode encoding issues for Windows console compatibility
- Enhanced error handling and logging throughout the system
- Improved database transaction management
- Better API parameter handling for GPT-5 compatibility
- Enhanced financial data extraction from Companies House
- Improved location discovery and analysis

### New Integrations
- Google Maps Places API v1 for comprehensive location discovery
- iXBRL document parsing for detailed financial analysis
- Enhanced competitor identification and campaign creation

### UI/UX Improvements
- Added "View All Leads" functionality
- Enhanced customer detail views with financial and location data
- Improved navigation with additional "View Leads" buttons
- Better error handling and user feedback

## 🐛 Troubleshooting

### Common Issues

1. **Unicode Encoding Errors**:
   - Fixed in v1.1.0 - ensure you're running the latest version

2. **API Key Issues**:
   - Verify all API keys are configured in database settings
   - Check API key permissions and quotas

3. **Database Locking**:
   - Enhanced transaction management in v1.1.0
   - Restart application if issues persist

4. **Background Processing**:
   - Campaigns now run in separate processes
   - Should survive Flask reloads

## 📝 Changelog

### Version 1.1.0 (Current)
- Added Google Maps Places API v1 integration
- Enhanced financial data extraction with iXBRL parsing
- Improved location discovery and analysis
- Added competitor campaign creation
- Enhanced UI with "View All Leads" functionality
- Fixed Unicode encoding issues
- Improved background processing
- Enhanced error handling and logging

### Version 1.0.0
- Initial release
- Basic lead generation with GPT-5-mini
- Companies House integration
- LinkedIn data extraction
- Customer management system
- Quote generation system

## 🤝 Support

This is a proprietary system for CCS. For technical support or feature requests, please contact the development team.

## 📄 License

Private - All rights reserved. This software is proprietary to CCS and not available for public use or distribution.

---

**Version 1.1.0** - Enhanced with Google Maps integration, improved financial analysis, and comprehensive location intelligence.