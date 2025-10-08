# CCS Quote Tool - Complete Project Specification

## Project Overview
A Flask-based web application for generating structured cabling quotations using AI analysis. The system provides automated project analysis, material calculations, labour estimates, and professional quotation generation.

## Current Status
**Version**: 1.1  
**Last Updated**: December 19, 2024  
**Status**: Production Ready - Enhanced with Flexible AI Analysis

## Core Features

### 1. AI-Powered Quote Analysis
- **OpenAI Integration**: Uses GPT-4o-mini for intelligent project analysis
- **Flexible Project Types**: Handles WiFi, CCTV, door entry, structured cabling, and combined projects
- **Intelligent Analysis**: Reads actual project descriptions instead of making assumptions
- **Structured Output**: JSON-formatted responses with consistent data structure
- **Product Recommendations**: Specific product suggestions with pricing when available
- **Clarification Questions**: AI can ask up to 5 clarifying questions for missing details
- **Brand Preferences**: Configurable preferred brands (Connectix, Unifi, Paxton Net2, etc.)
- **Internet Pricing**: Fallback to web-based pricing when local data unavailable
- **Complete Debugging**: Full JSON response display for troubleshooting

### 2. Labour Calculation System
- **Daily Rate Based**: Uses configurable day rate for pair of engineers (£300-£600+)
- **Smart Rounding Rules**:
  - < 8 hours: Round up to nearest half day (0.5 days)
  - ≥ 8 hours: Round up to nearest full day
- **Accurate Calculations**: 
  - Twin outlets = 2 connections each
  - Quad outlets = 4 connections each
  - Example: 40 twin + 4 quad + 10 twin = 116 total connections

### 3. Material Management
- **Comprehensive Lists**: Includes all necessary materials (cables, connectors, face plates, back boxes, etc.)
- **Realistic Quantities**: 
  - RJ45 connectors = total connections
  - Face plates = outlet locations
  - Back boxes = outlet locations  
  - Patch panels = connections ÷ 24 (round up)
  - Cable = 25-30m per outlet + 10% waste, round up to boxes
- **Fiber Detection**: Automatically includes fiber for distances >90m (copper limit)

### 4. Travel & Distance Calculation
- **Google Maps Integration**: Calculates travel distance and time
- **UK Standards**: Displays distances in miles (not km)
- **Cost Calculation**: Configurable cost per mile (£0.45 default)
- **Export Options**: Can include travel costs in Word documents

### 5. User Interface & Experience
- **Clean Design**: Bootstrap-based responsive interface
- **Real-time Analysis**: Live AI analysis with loading indicators
- **Form Auto-population**: AI results populate form fields automatically
- **Original Text Display**: Shows original project specification for reference
- **Professional Quotations**: Word document generation with company branding
- **Complete Data Visibility**: Full JSON response display for debugging and transparency
- **Enhanced Product Display**: Tabular format with pricing information
- **Flexible Project Handling**: UI adapts to different project types (WiFi, CCTV, etc.)

## Technical Architecture

### Backend (Flask)
- **Framework**: Flask 2.3+ with SQLAlchemy ORM
- **Database**: SQLite (production-ready, can be upgraded to PostgreSQL)
- **Authentication**: Flask-Login with role-based access (Admin/User)
- **API Integration**: 
  - OpenAI API (GPT-4o-mini)
  - Google Maps API (Directions)
- **File Generation**: Python-docx for Word documents

### Database Schema
```sql
-- Core Tables
Users (id, username, email, password_hash, is_admin)
Quotes (id, quote_number, client_name, client_email, project_title, 
        project_description, site_address, building_type, building_size,
        number_of_floors, number_of_rooms, cabling_type, wifi_requirements,
        cctv_requirements, door_entry_requirements, special_requirements,
        ai_analysis, recommended_products, estimated_time, alternative_solutions,
        clarifications_log, labour_breakdown, quotation_details, created_by,
        created_at, updated_at, quote_data, estimated_cost,
        travel_distance_km, travel_time_minutes, travel_cost,
        company_name, company_address, company_postcode)

-- Configuration Tables  
APISettings (id, service_name, api_key, is_active)
AdminSetting (id, key, value, updated_at)
PricingItem (id, name, category, unit_price, source, last_updated)
Template (id, name, content, is_default)

-- AI Management
AIPrompt (id, prompt_type, name, description, system_prompt, 
          user_prompt_template, variables, is_default, is_active)
AIPromptHistory (id, prompt_id, name, content, created_at)
```

### Frontend Architecture
- **Templates**: Jinja2 with Bootstrap 5
- **JavaScript**: Vanilla JS with modern ES6+ features
- **AJAX**: Fetch API for real-time AI analysis
- **Responsive Design**: Mobile-first approach
- **UI Components**: 
  - Loading spinners and progress indicators
  - Modal dialogs for clarifications
  - Real-time form validation
  - Dynamic content updates

## Configuration & Settings

### Admin Settings (AdminSetting table)
- `day_rate`: Daily rate for pair of engineers (default: £300)
- `cost_per_mile`: Travel cost per mile (default: £0.45)
- `company_name`: Company name for quotes
- `company_address`: Company address for distance calculations
- `company_postcode`: Company postcode
- `cabling_brands`: Preferred cabling brands (Connectix,Excel,HellermannTyton)
- `cctv_brands`: Preferred CCTV brands (Unifi,Hikvision,Dahua)
- `wifi_brands`: Preferred WiFi brands (Unifi,Cisco,Meraki)
- `door_entry_brands`: Preferred door entry brands (Paxton Net2,Unifi,2N)
- `patch_panel_brands`: Preferred patch panel brands (Connectix,Excel,Panduit)
- `fiber_brands`: Preferred fiber optic brands (Corning,CommScope,ADC)
- `cabinet_brands`: Preferred cabinet brands (Connectix,Excel,Rittal)

### API Configuration
- **OpenAI**: Requires API key with GPT-4o-mini access
- **Google Maps**: Requires Directions API access
- **Rate Limits**: Configured for production usage
- **Error Handling**: Graceful fallbacks for API failures

## AI Prompt Engineering

### Current Prompt Structure (Flexible Analysis)
```
You are an experienced IT and communications contractor with expertise in:
- Structured cabling (Cat5e/Cat6/Cat6a/fiber)
- WiFi networks and access points
- CCTV surveillance systems
- Door entry and access control
- Network infrastructure and equipment

Analyze each project based on its actual requirements. Don't assume project types - read the description carefully.
Provide specific product recommendations with pricing when possible.

**Project Details:**
[Project information from form]

**Analysis Instructions:**
1. READ THE PROJECT DESCRIPTION CAREFULLY - don't make assumptions
2. Identify what is actually being requested (WiFi, CCTV, door entry, cabling, or combination)
3. Calculate materials and labour based on the actual requirements
4. Recommend specific products with pricing when possible
5. Ask clarification questions if critical details are missing

**For Different Project Types:**
- WiFi Projects: Include access points, controllers, cabling, power requirements
- CCTV Projects: Include cameras, recorders, monitors, cabling, storage
- Door Entry Projects: Include access control, readers, locks, cabling, software
- Structured Cabling: Include cables, connectors, face plates, patch panels, cabinets
- Combined Projects: Include all relevant systems and their integration

**Labour Rate:** £[day_rate] per pair of engineers per day (8-hour day)

Return comprehensive JSON with ALL relevant information including pricing...
```

### JSON Response Format (Enhanced)
```json
{
  "analysis": "Detailed analysis of what the project actually involves",
  "products": [
    {
      "item": "UniFi WiFi 6 Access Point",
      "quantity": 3,
      "unit_price": 89.99,
      "total_price": 269.97,
      "notes": "WiFi 6 coverage for 10 rooms and meeting room"
    },
    {
      "item": "Cat5e Cable",
      "quantity": 2,
      "unit_price": 45.00,
      "total_price": 90.00,
      "notes": "305m boxes for access point cabling"
    }
  ],
  "alternatives": [
    {
      "solution": "Wireless mesh network",
      "pros": "Easier installation, no cabling required",
      "cons": "Potentially less reliable than wired connections",
      "cost_difference": "Lower initial cost"
    }
  ],
  "estimated_time": 2,
  "labour_breakdown": [
    {
      "task": "Install WiFi access points and cabling",
      "days": 2,
      "engineer_count": 2,
      "day_rate": 300,
      "cost": 600,
      "notes": "For 10 rooms and meeting room WiFi installation"
    }
  ],
  "clarifications": ["What is the exact layout of the rooms for optimal access point placement?"],
  "quotation": {
    "client_requirement": "Install WiFi access points with structured cabling in an office with 10 rooms and a large meeting room",
    "scope_of_works": [
      "Install WiFi access points in strategic locations",
      "Run Cat5e cabling to each access point",
      "Configure and test WiFi network"
    ],
    "materials": [
      {
        "item": "UniFi WiFi 6 Access Point",
        "quantity": 3,
        "unit_price": 89.99,
        "total_price": 269.97,
        "notes": "Professional WiFi 6 access points"
      }
    ],
    "labour": {
      "engineers": 2,
      "days": 2,
      "day_rate": 300,
      "total_cost": 600,
      "notes": "Installation and configuration by pair of engineers"
    },
    "assumptions_exclusions": [
      "Assumes existing network infrastructure available",
      "Excludes network switches and additional equipment"
    ]
  },
  "travel_distance_miles": 9.6,
  "travel_time_minutes": 32
}
```

## File Structure
```
CCS quote tool/
├── app.py                          # Main Flask application
├── models.py                       # SQLAlchemy database models
├── requirements.txt                # Python dependencies
├── requirements_simple.txt         # Simplified dependency list
├── PROJECT_SPECIFICATION.md        # This document
├── PROJECT_STATUS_AND_NEXT_STEPS.md # Previous status document
├── routes/
│   ├── main.py                    # Main application routes
│   ├── admin.py                   # Admin panel routes
│   ├── api.py                     # API endpoints
│   └── api_simple.py              # Simplified API endpoints
├── templates/
│   ├── base.html                  # Base template
│   ├── create_quote.html          # Quote creation form
│   ├── view_quote.html            # Quote viewing page
│   ├── login.html                 # Authentication
│   ├── admin/
│   │   ├── dashboard.html         # Admin dashboard
│   │   ├── api_settings.html      # API configuration
│   │   └── ai_prompts.html        # AI prompt management
│   └── components/
│       └── clarification_modal.html # Question/answer modal
├── utils/
│   ├── ai_helper.py               # OpenAI integration
│   ├── ai_pricing_extractor.py    # AI-powered pricing extraction
│   ├── pricing_helper.py          # Quote pricing calculations
│   └── document_generator.py      # Word document generation
├── scripts/
│   ├── populate_default_prompts.py           # Original AI prompt initialization
│   ├── populate_default_prompts_simple.py    # Simplified prompts
│   ├── populate_default_prompts_flexible.py  # Flexible multi-project prompts (CURRENT)
│   ├── populate_brand_preferences.py         # Brand settings initialization
│   ├── populate_admin_settings.py            # Admin settings initialization
│   └── reset_db.py                           # Database reset utility
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── ccs_quotes.db                  # SQLite database
```

## Installation & Setup

### Prerequisites
- Python 3.11+ (tested on 3.13)
- OpenAI API key
- Google Maps API key (optional)

### Installation Steps
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up database: `python scripts/reset_db.py`
4. Configure API keys in admin panel
5. Run application: `python app.py`

### Environment Configuration
- **Debug Mode**: Enabled for development
- **Database**: SQLite (file-based, no server required)
- **Port**: 5000 (configurable)
- **Host**: 0.0.0.0 (all interfaces)

## Key Algorithms & Calculations

### Connection Calculation
```python
def calculate_connections(outlet_spec):
    """
    Calculate total connections from outlet specification
    Example: "40 twin + 4 quad + 10 twin" = 116 connections
    """
    connections = 0
    # Twin outlets = 2 connections each
    connections += twin_count * 2
    # Quad outlets = 4 connections each  
    connections += quad_count * 4
    # Single outlets = 1 connection each
    connections += single_count * 1
    return connections
```

### Labour Rounding Rules
```python
def round_labour_hours(hours):
    """
    Round labour hours to days based on business rules
    """
    if hours < 8:
        return 0.5  # Half day minimum
    elif hours >= 8:
        return math.ceil(hours / 8)  # Round up to full days
```

### Material Calculations
```python
def calculate_materials(connections, outlet_locations):
    """
    Calculate required materials based on connections and locations
    """
    materials = {
        'rj45_connectors': connections,
        'face_plates': outlet_locations,
        'back_boxes': outlet_locations,
        'patch_panels': math.ceil(connections / 24),
        'cable_boxes': math.ceil((connections * 25 * 1.1) / 305)  # 305m boxes
    }
    return materials
```

## Error Handling & Logging

### API Error Handling
- OpenAI API failures: Graceful degradation with error messages
- Google Maps API failures: Continue without travel calculations
- Network timeouts: 30-second timeout with retry logic
- Rate limiting: Respect API limits with backoff

### Database Error Handling
- Connection failures: Automatic retry with exponential backoff
- Data validation: Input sanitization and type checking
- Transaction rollback: Automatic rollback on errors

### User Error Handling
- Form validation: Client-side and server-side validation
- File upload errors: Clear error messages
- Authentication errors: Secure error handling

## Security Considerations

### Authentication & Authorization
- Password hashing: Werkzeug security with salt
- Session management: Flask-Login with secure cookies
- Role-based access: Admin vs. User permissions
- CSRF protection: Flask-WTF integration

### Data Protection
- Input sanitization: All user inputs sanitized
- SQL injection prevention: SQLAlchemy ORM protection
- XSS prevention: Jinja2 auto-escaping
- API key security: Encrypted storage in database

### Production Security
- HTTPS enforcement: SSL/TLS configuration
- Secure headers: Security headers middleware
- Rate limiting: API rate limiting implementation
- Audit logging: User action logging

## Performance Optimizations

### Database Optimizations
- Indexed queries: Proper database indexing
- Connection pooling: Efficient database connections
- Query optimization: Minimal N+1 queries
- Caching: Redis integration (future enhancement)

### API Optimizations
- Response caching: AI response caching
- Batch processing: Multiple API calls in parallel
- Connection pooling: HTTP connection reuse
- Compression: Response compression

### Frontend Optimizations
- Asset minification: CSS/JS minification
- Image optimization: WebP format support
- Lazy loading: Deferred resource loading
- CDN integration: Static asset CDN (future)

## Testing Strategy

### Unit Testing
- Model testing: Database model validation
- API testing: Endpoint functionality
- Utility testing: Helper function validation
- Calculation testing: Business logic verification

### Integration Testing
- API integration: External API testing
- Database integration: Data persistence testing
- User workflow: End-to-end testing
- Error scenario: Failure case testing

### Performance Testing
- Load testing: Concurrent user simulation
- Stress testing: System limits testing
- Database performance: Query optimization testing
- API performance: Response time testing

## Deployment Considerations

### Production Deployment
- **Web Server**: Gunicorn or uWSGI
- **Database**: PostgreSQL for production
- **Reverse Proxy**: Nginx for static files and SSL
- **Process Management**: Supervisor or systemd
- **Monitoring**: Application monitoring and logging
- **Backup Strategy**: Automated database backups

### Scaling Considerations
- **Horizontal Scaling**: Multiple application instances
- **Database Scaling**: Read replicas and connection pooling
- **Caching Layer**: Redis for session and data caching
- **Load Balancing**: Multiple server load balancing
- **CDN Integration**: Static asset delivery optimization

## Future Enhancements

### Planned Features
1. **Advanced Analytics**: Quote analytics and reporting
2. **Multi-currency Support**: International pricing
3. **Template System**: Customizable quote templates
4. **Email Integration**: Automated quote delivery
5. **Mobile App**: Native mobile application
6. **API Versioning**: RESTful API for third-party integration
7. **Advanced AI**: More sophisticated project analysis
8. **Inventory Management**: Stock level integration
9. **Customer Portal**: Self-service quote viewing
10. **Integration Hub**: CRM and accounting system integration

### Technical Improvements
1. **Microservices Architecture**: Service decomposition
2. **Container Deployment**: Docker containerization
3. **CI/CD Pipeline**: Automated testing and deployment
4. **Monitoring Dashboard**: Real-time system monitoring
5. **Performance Metrics**: Detailed performance tracking
6. **Security Audit**: Regular security assessments
7. **Code Quality**: Automated code quality checks
8. **Documentation**: API documentation generation

## Recent Updates & Improvements

### Version 1.1 - Flexible AI Analysis (December 19, 2024)

#### **Major Enhancements:**
1. **Flexible Project Type Handling**
   - AI now analyzes actual project requirements instead of assuming structured cabling
   - Supports WiFi, CCTV, door entry, structured cabling, and combined projects
   - Intelligent project type detection based on description

2. **Enhanced Product Recommendations**
   - Specific product suggestions with model numbers
   - Pricing information included when available
   - Detailed specifications and reasoning
   - Market pricing integration

3. **Complete Data Visibility**
   - Full JSON response display for debugging
   - Enhanced product display with pricing tables
   - Better error handling and validation
   - Transparent AI decision making

4. **Improved User Experience**
   - More intelligent clarification questions
   - Better project analysis accuracy
   - Enhanced debugging capabilities
   - Flexible UI adaptation to different project types

#### **Technical Changes:**
- New flexible prompt system (`populate_default_prompts_flexible.py`)
- Enhanced frontend display with pricing information
- Improved JSON response structure with pricing fields
- Better error handling and data validation

#### **Key Benefits:**
- ✅ **Accurate Project Analysis**: AI reads actual requirements
- ✅ **Multi-Project Support**: Handles any IT/communications project type
- ✅ **Product Pricing**: Includes specific products with pricing
- ✅ **Better Debugging**: Complete data visibility
- ✅ **Improved Accuracy**: No more incorrect assumptions

## Troubleshooting Guide

### Common Issues
1. **AI Analysis Hanging**: Check OpenAI API key and network connectivity
2. **Database Errors**: Verify SQLite file permissions and integrity
3. **Template Errors**: Check Jinja2 syntax and variable names
4. **API Failures**: Verify external API keys and rate limits
5. **Performance Issues**: Check database queries and API response times

### Debug Mode
- Enable Flask debug mode for development
- Use browser developer tools for frontend debugging
- Check application logs for backend issues
- Use database browser for data inspection

### Support Resources
- Application logs: `/var/log/ccs-quote-tool/`
- Database file: `ccs_quotes.db`
- Configuration: Admin panel settings
- API documentation: Built-in API endpoints

## Conclusion

The CCS Quote Tool is a comprehensive, production-ready application that successfully combines AI-powered analysis with practical business requirements. The system provides accurate quotations, professional documentation, and a user-friendly interface for structured cabling projects.

The architecture is designed for scalability, maintainability, and extensibility, with clear separation of concerns and modern development practices. The AI integration provides intelligent analysis while maintaining accuracy and consistency in calculations.

For continued development, focus on the planned enhancements and technical improvements outlined above, while maintaining the core functionality and user experience that makes the system effective for real-world use.

---

**Document Version**: 1.1  
**Last Updated**: December 19, 2024  
**Maintained By**: Development Team  
**Next Review**: As needed for feature updates
