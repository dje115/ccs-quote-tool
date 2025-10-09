# CCS Quote Tool - Version 1.2
## Comprehensive Project Documentation

### 🚀 **Project Overview**
A world-class CRM and quoting tool with AI-powered lead generation, customer intelligence, and comprehensive business management features.

### 📋 **Recent Major Updates (v1.2)**

#### **🔧 Bug Fixes & Improvements**
- **Fixed Website Field Bug**: Addresses were incorrectly stored in website fields during address-based campaigns
- **Fixed Pagination Error**: Resolved Jinja2 template conflict in leads pagination
- **Enhanced Route Management**: Fixed double prefix issues in CRM routes
- **Improved Data Validation**: Added website URL validation in lead conversion

#### **🎯 New Features Added**
- **Enhanced CRM Dashboard**: Added "Converted Leads" button and comprehensive filters bar
- **Dynamic Filters System**: Quote management, follow-up tracking, AI analysis filters
- **Address Management**: Exclude/include addresses, manual address addition
- **Google Maps Integration**: Enhanced location discovery with UK-wide searches
- **Financial Data Enhancement**: Improved iXBRL parsing and Companies House integration
- **Contact Management**: Add contacts from Companies House director data

#### **🤖 AI & Automation**
- **GPT-5 Integration**: Full migration to GPT-5 models (gpt-5, gpt-5-mini)
- **Enhanced Lead Generation**: Improved web search and competitor analysis
- **Batch AI Processing**: Background AI analysis for multiple customers
- **Smart Address Filtering**: AI-powered location validation

### 🗄️ **Database Schema**

#### **Core Tables**
```sql
-- Users and Authentication
users (id, username, email, password_hash, is_admin, created_at)

-- CRM System
customers (
    id, company_name, status, business_sector, business_size_category,
    website, company_registration, registration_confirmed,
    billing_address, billing_postcode, shipping_address, shipping_postcode,
    primary_address, ai_analysis_raw, linkedin_url, linkedin_data,
    companies_house_data, website_data, google_maps_data,
    manual_addresses, excluded_addresses, created_by, created_at, updated_at
)

contacts (
    id, customer_id, first_name, last_name, job_title, role,
    email, phone, notes, created_at, updated_at
)

customer_interactions (
    id, customer_id, interaction_type, subject, notes,
    follow_up_date, created_by, created_at
)

-- Lead Generation System
lead_generation_campaigns (
    id, name, description, prompt_type, postcode, distance_miles,
    max_results, status, custom_search_criteria, search_criteria_used,
    created_by, started_at, completed_at, created_at
)

leads (
    id, campaign_id, company_name, website, address, postcode,
    business_sector, company_size, contact_name, contact_email,
    contact_phone, contact_title, status, lead_score,
    potential_project_value, timeline_estimate, ai_analysis,
    linkedin_url, linkedin_data, companies_house_data, website_data,
    converted_to_customer_id, created_by, created_at, updated_at
)

lead_interactions (
    id, lead_id, interaction_type, subject, notes,
    follow_up_date, created_by, created_at
)

lead_generation_prompts (
    id, name, prompt_type, description, requires_company_name,
    created_by, created_at
)

-- Quoting System
quotes (
    id, customer_id, quote_number, title, description,
    status, total_amount, valid_until, created_by, created_at, updated_at
)

pricing_items (
    id, quote_id, description, quantity, unit_price,
    total_price, created_at
)

templates (
    id, name, description, content, is_default, created_by, created_at
)

-- Configuration
api_settings (
    id, service_name, api_key, api_url, is_active, created_at, updated_at
)

ai_prompts (
    id, name, prompt_type, content, is_active, created_by, created_at
)
```

#### **Key Relationships**
- `customers` → `contacts` (1:many)
- `customers` → `customer_interactions` (1:many)
- `customers` → `quotes` (1:many)
- `leads` → `lead_interactions` (1:many)
- `leads` → `customers` (conversion tracking)
- `campaigns` → `leads` (1:many)

### 🛠️ **Development Setup**

#### **Prerequisites**
- Python 3.13+
- SQLite (included with Python)
- OpenAI API Key (GPT-5 access required)
- Companies House API Key
- Google Maps API Key (optional)

#### **Installation**
```bash
# Clone repository
git clone [repository-url]
cd ccs-quote-tool

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-gpt-5-api-key"
export COMPANIES_HOUSE_API_KEY="your-companies-house-key"
export GOOGLE_MAPS_API_KEY="your-google-maps-key"

# Run application
python app.py
```

#### **Database Initialization**
The database is automatically created and initialized on first run with:
- Default admin user (admin/admin123)
- Required tables and relationships
- Sample data templates

### 🔧 **Key Configuration**

#### **API Settings**
- **OpenAI**: GPT-5 models only (gpt-5, gpt-5-mini)
- **Companies House**: Document API + Main API
- **Google Maps**: Places API v1 (Text Search + Place Details)

#### **File Structure**
```
ccs-quote-tool/
├── app.py                 # Main Flask application
├── models.py             # Core database models
├── models_crm.py         # CRM-specific models
├── models_lead_generation.py # Lead generation models
├── routes/               # Flask route blueprints
│   ├── main.py          # Main application routes
│   ├── crm.py           # CRM functionality
│   ├── lead_generation.py # Lead generation system
│   ├── api.py           # API endpoints
│   └── admin.py         # Admin functions
├── utils/                # Utility services
│   ├── ai_helper.py     # AI integration
│   ├── lead_generation_service.py # Lead generation logic
│   ├── customer_intelligence.py # Customer analysis
│   └── external_data_service.py # External API integration
├── templates/            # Jinja2 templates
│   ├── crm/             # CRM templates
│   ├── lead_generation/ # Lead generation templates
│   └── base.html        # Base template
└── static/              # Static assets
```

### 🚀 **Core Features**

#### **Lead Generation System**
- **AI-Powered Discovery**: GPT-5 with web search capabilities
- **Campaign Management**: Create and manage lead generation campaigns
- **Address-Based Campaigns**: Generate leads from specific locations
- **Competitor Analysis**: Identify and verify competitor companies
- **Deduplication**: Smart duplicate detection across campaigns and CRM

#### **CRM System**
- **Customer Management**: Comprehensive customer profiles
- **Contact Management**: Multiple contacts per customer
- **AI Analysis**: Automated customer intelligence gathering
- **Companies House Integration**: Financial data and director information
- **Google Maps Integration**: Location discovery and verification

#### **Quoting System**
- **Dynamic Quotes**: Create and manage customer quotes
- **Template System**: Reusable quote templates
- **Pricing Management**: Flexible pricing item management
- **Status Tracking**: Quote lifecycle management

### 🔍 **Recent Technical Improvements**

#### **Error Handling**
- Unicode encoding fixes for Windows console
- Robust API error handling
- Database transaction management
- Template error resolution

#### **Performance Optimizations**
- Background processing for long-running tasks
- Efficient database queries
- Caching strategies for external API calls
- Async processing for AI operations

#### **Security Enhancements**
- Input validation and sanitization
- SQL injection prevention
- API key management
- User authentication and authorization

### 📊 **Monitoring & Debugging**

#### **Logging**
- Comprehensive debug logging throughout the application
- API call tracking and error reporting
- Database operation logging
- Background task monitoring

#### **Error Tracking**
- Detailed error messages with context
- Stack trace logging for debugging
- User-friendly error pages
- API response validation

### 🔄 **Development Workflow**

#### **Code Organization**
- Modular blueprint architecture
- Separation of concerns (routes, models, utils)
- Consistent naming conventions
- Comprehensive documentation

#### **Testing Strategy**
- Manual testing procedures
- API endpoint validation
- Database integrity checks
- User workflow testing

### 📈 **Future Development Ideas**

#### **Immediate Enhancements**
- Sales pipeline visualization (Kanban board)
- Advanced reporting and analytics
- Email integration and automation
- Mobile responsiveness improvements

#### **Medium-term Features**
- Multi-user support with role-based access
- Advanced AI features (predictive analytics)
- Integration with accounting software
- Automated follow-up systems

#### **Long-term Vision**
- Mobile application
- API for third-party integrations
- Advanced business intelligence
- Enterprise-grade security and scalability

### 🐛 **Known Issues & Limitations**
- Some external API rate limits
- Background task monitoring could be improved
- Mobile interface needs optimization
- Advanced reporting features pending implementation

### 📞 **Support & Maintenance**
- Regular database backups recommended
- API key rotation procedures
- Performance monitoring guidelines
- User training documentation

---

**Last Updated**: October 9, 2025
**Version**: 1.2
**Status**: Production Ready
