# Changelog
## CCS Quote Tool

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-10-09

### 🎯 **Added**
- **Enhanced CRM Dashboard**
  - Added "Converted Leads" button for viewing leads converted to CRM customers
  - Implemented comprehensive dynamic filters bar with organized categories
  - Added quote management filters (Draft, Sent, Accepted)
  - Added follow-up tracking filters (Overdue, Due Today, This Week)
  - Added AI analysis filters (Pending, Needs Update, Batch Processing)
  - Added high-value customer and quote filters
  - Added business sector filtering (Technology, Healthcare, Education)
  - Added export and reporting action buttons

- **Address Management System**
  - Added "Not this business" checkbox functionality for Google Maps locations
  - Implemented address exclusion/inclusion system with JSON storage
  - Added manual address addition capability
  - Added address selection for targeted lead generation campaigns
  - Added "Add Selected" functionality for creating campaigns from specific addresses

- **Contact Management Enhancement**
  - Added "Add as Contact" button for Companies House director data
  - Implemented contact creation from director information
  - Added proper name parsing for "Last, First" format handling
  - Added contact role selection and validation

- **Google Maps Integration Enhancement**
  - Expanded search to cover all UK regions and counties
  - Added Scotland and Northern Ireland coverage
  - Implemented comprehensive location filtering and validation
  - Added "Open in Google Maps" links throughout the application
  - Enhanced location data storage and display

- **Template System Improvements**
  - Added `dict_filter` template filter for removing duplicate parameters
  - Enhanced JSON template filters for better data handling
  - Improved template error handling and debugging

### 🔧 **Changed**
- **Lead Generation System**
  - Enhanced address-based campaign creation to prevent address storage in website fields
  - Improved lead conversion validation with website URL checking
  - Enhanced competitor verification prompts and data collection
  - Updated deduplication logic for better lead management

- **CRM Route Management**
  - Fixed double prefix issues in CRM blueprint routes
  - Standardized route naming conventions
  - Improved route organization and maintainability

- **Database Schema**
  - Added `excluded_addresses` JSON field to customers table
  - Added `manual_addresses` JSON field to customers table
  - Enhanced Companies House data storage structure
  - Improved Google Maps data storage format

- **User Interface**
  - Redesigned CRM dashboard with modern filter system
  - Added animated filter buttons with hover effects
  - Improved responsive design for better mobile experience
  - Enhanced visual organization with color-coded sections

### 🐛 **Fixed**
- **Website Field Bug**
  - Fixed critical bug where physical addresses were stored in website fields during address-based campaigns
  - Added website URL validation in lead conversion process
  - Implemented proper address vs URL distinction logic
  - Cleaned existing customer data with incorrect website fields

- **Pagination Error**
  - Fixed Jinja2 template conflict causing "multiple values for keyword argument 'page'" error
  - Implemented proper parameter filtering in pagination links
  - Added template filter to prevent duplicate URL parameters

- **Route Conflicts**
  - Resolved 404 errors in CRM address management routes
  - Fixed blueprint prefix duplication issues
  - Corrected route parameter handling

- **Data Validation**
  - Enhanced input validation for contact creation
  - Improved error handling for external API calls
  - Added proper null checking for data processing

- **Unicode Handling**
  - Fixed Unicode encoding issues in Windows console output
  - Replaced special characters with ASCII equivalents in logging
  - Improved error message encoding for better debugging

### 🗑️ **Removed**
- Deprecated website field usage for address storage
- Redundant route prefixes causing conflicts
- Unused template parameters and variables
- Temporary debugging files and scripts

### 🔒 **Security**
- Enhanced input validation and sanitization
- Improved API key management and storage
- Added proper error handling to prevent information leakage
- Strengthened database query parameterization

### 📊 **Performance**
- Optimized database queries for better response times
- Improved background task processing
- Enhanced caching strategies for external API calls
- Reduced redundant API requests through better data management

### 🧪 **Technical Improvements**
- Enhanced error logging and debugging capabilities
- Improved code organization and modularity
- Added comprehensive documentation and comments
- Implemented better separation of concerns

### 📱 **Mobile & Accessibility**
- Improved responsive design for mobile devices
- Enhanced touch-friendly interface elements
- Better accessibility for screen readers
- Optimized loading times for mobile connections

## [1.1.0] - 2025-09-XX

### 🎯 **Added**
- Initial GPT-5 integration and migration from GPT-4
- Companies House API integration with financial data extraction
- Google Maps Places API integration for location discovery
- Lead generation system with AI-powered web search
- Basic CRM functionality with customer management
- Quote system with template support

### 🔧 **Changed**
- Migrated from GPT-4 to GPT-5 models exclusively
- Enhanced AI prompt engineering for better lead generation
- Improved external API integration architecture

### 🐛 **Fixed**
- Initial API integration issues
- Database schema inconsistencies
- Template rendering problems

## [1.0.0] - 2025-08-XX

### 🎯 **Added**
- Initial application structure
- Basic Flask application setup
- SQLite database integration
- User authentication system
- Basic quoting functionality
- Admin panel for system management

---

## 🚀 **Upcoming Features (Version 1.3)**

### **Planned Additions**
- Sales pipeline visualization with Kanban board
- Advanced reporting and analytics dashboard
- Email integration and automation
- Mobile application development
- Multi-user support with role-based access
- Advanced AI features and predictive analytics

### **Technical Improvements**
- PostgreSQL migration for better performance
- API platform for third-party integrations
- Enhanced security and compliance features
- Performance optimization and caching
- Advanced workflow automation

---

## 📝 **Migration Notes**

### **From Version 1.1 to 1.2**
- No breaking changes to existing functionality
- Database schema additions are backward compatible
- Existing customer data automatically migrated
- API endpoints remain unchanged

### **Configuration Updates**
- No new environment variables required
- Existing API keys continue to work
- Database automatically updated on startup

### **User Impact**
- Enhanced dashboard provides better user experience
- New filter system improves workflow efficiency
- Address management reduces data quality issues
- Contact creation streamlines customer management

---

**Version 1.2.0 represents a significant enhancement to the CCS Quote Tool, focusing on user experience improvements, data quality fixes, and advanced CRM functionality. The enhanced dashboard and filtering system provides a solid foundation for future development phases.**

**Last Updated**: October 9, 2025
**Next Version**: 1.3.0 (Planned for November 2025)
