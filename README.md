# CCS Quote Tool - Version 1.2
## World-Class CRM & Quoting Platform

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/your-repo/ccs-quote-tool)
[![Python](https://img.shields.io/badge/python-3.13+-green.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.0.0-red.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive Customer Relationship Management (CRM) and quoting platform with AI-powered lead generation, customer intelligence, and advanced business management features.

## 🚀 **Key Features**

### **🤖 AI-Powered Lead Generation**
- **GPT-5 Integration**: Advanced AI with web search capabilities
- **Intelligent Campaigns**: Automated lead discovery and qualification
- **Competitor Analysis**: Identify and verify competitor companies
- **Address-Based Campaigns**: Generate leads from specific locations
- **Smart Deduplication**: Prevent duplicate leads across campaigns

### **📊 Advanced CRM System**
- **Customer Intelligence**: AI-powered customer analysis and insights
- **Companies House Integration**: Financial data and director information
- **Google Maps Integration**: Location discovery and verification
- **Contact Management**: Multiple contacts per customer with role tracking
- **Interaction History**: Complete customer communication tracking

### **💰 Professional Quoting System**
- **Dynamic Quotes**: Create and manage customer quotes
- **Template System**: Reusable quote templates
- **Pricing Management**: Flexible pricing item management
- **Status Tracking**: Complete quote lifecycle management

### **📈 Enhanced Dashboard**
- **Real-time Analytics**: Live dashboard with key performance indicators
- **Smart Filters**: Comprehensive filtering system for leads, customers, and quotes
- **Quick Actions**: One-click access to common tasks
- **Visual Analytics**: Interactive charts and data visualization

## 🛠️ **Quick Start**

### **Prerequisites**
- Python 3.13 or higher
- OpenAI API Key (GPT-5 access required)
- Companies House API Key
- Google Maps API Key (optional but recommended)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/ccs-quote-tool.git
   cd ccs-quote-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-gpt-5-api-key"
   export COMPANIES_HOUSE_API_KEY="your-companies-house-key"
   export GOOGLE_MAPS_API_KEY="your-google-maps-key"
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - URL: http://localhost:5000
   - Admin login: `admin` / `admin123`

## 📋 **System Requirements**

### **Minimum Requirements**
- **OS**: Windows 10+, macOS 10.15+, or Linux
- **Python**: 3.13 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space
- **Network**: Internet connection for API calls

### **Recommended Configuration**
- **RAM**: 16GB for optimal performance
- **Storage**: SSD with 10GB free space
- **Network**: Stable broadband connection
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

## 🗄️ **Database Schema**

The application uses SQLite with the following key tables:

- **`customers`**: Main customer data with AI analysis
- **`contacts`**: Customer contact information
- **`leads`**: Generated leads with conversion tracking
- **`lead_generation_campaigns`**: Campaign management
- **`quotes`**: Customer quotes and pricing
- **`users`**: User authentication and management

For detailed schema information, see [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md).

## 🔧 **Configuration**

### **API Configuration**
The application requires the following API keys:

1. **OpenAI API Key**
   - Required for GPT-5 AI features
   - Must have access to GPT-5 models (not GPT-4)
   - Configure in the admin panel or environment variables

2. **Companies House API Key**
   - Required for UK company data retrieval
   - Free tier available from Companies House
   - Configure in the admin panel

3. **Google Maps API Key**
   - Optional but recommended for location services
   - Requires Places API access
   - Configure in the admin panel

### **Database Configuration**
- **Default**: SQLite database (`ccs_quotes.db`)
- **Automatic**: Database creation and migration on startup
- **Backup**: Regular backups recommended for production use

## 📖 **Documentation**

- **[Project Documentation](PROJECT_DOCUMENTATION.md)**: Comprehensive technical documentation
- **[Development Guide](DEVELOPMENT_CONTINUATION_GUIDE.md)**: Development setup and continuation
- **[Future Ideas](FUTURE_DEVELOPMENT_IDEAS.md)**: Roadmap and feature planning
- **[Changelog](CHANGELOG.md)**: Version history and updates

## 🚀 **Usage Guide**

### **Getting Started**

1. **Login**: Use admin credentials to access the system
2. **Dashboard**: Review key metrics and quick actions
3. **Lead Generation**: Create campaigns to discover new prospects
4. **CRM Management**: Add and manage customer relationships
5. **Quote Creation**: Generate professional quotes for customers

### **Key Workflows**

#### **Lead Generation Process**
1. Navigate to Lead Generation dashboard
2. Create a new campaign with specific criteria
3. Run AI-powered lead discovery
4. Review and qualify generated leads
5. Convert qualified leads to customers

#### **Customer Management**
1. Access CRM dashboard
2. Use filters to find specific customers
3. Add contacts and interaction history
4. Run AI analysis for customer insights
5. Create quotes and track opportunities

#### **Quote Management**
1. Create quotes from customer records
2. Use templates for consistent formatting
3. Add pricing items and calculate totals
4. Send quotes to customers
5. Track quote status and follow-ups

## 🔒 **Security Features**

- **User Authentication**: Secure login system with password hashing
- **Input Validation**: Comprehensive data validation and sanitization
- **SQL Injection Prevention**: Parameterized queries throughout
- **API Security**: Secure API key storage and transmission
- **Error Handling**: Safe error messages without information leakage

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Application Won't Start**
```bash
# Check for running processes
taskkill /f /im python.exe

# Restart application
python app.py
```

#### **Database Issues**
- Verify `ccs_quotes.db` exists in project root
- Check file permissions and disk space
- Restart application for automatic migration

#### **API Issues**
- Verify API keys are valid and active
- Check internet connection
- Review API rate limits and quotas

#### **Template Errors**
- Clear browser cache and refresh
- Check browser console for JavaScript errors
- Verify template syntax and parameters

### **Getting Help**

1. Check the [Development Guide](DEVELOPMENT_CONTINUATION_GUIDE.md) for detailed troubleshooting
2. Review error messages in the application terminal
3. Check browser console for client-side errors
4. Verify API key configuration and permissions

## 🤝 **Contributing**

We welcome contributions to the CCS Quote Tool! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests if applicable**
5. **Submit a pull request**

### **Development Setup**
See [DEVELOPMENT_CONTINUATION_GUIDE.md](DEVELOPMENT_CONTINUATION_GUIDE.md) for detailed development setup instructions.

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 **Version History**

- **v1.2.0** (Current): Enhanced CRM dashboard, bug fixes, address management
- **v1.1.0**: GPT-5 integration, Companies House API, Google Maps
- **v1.0.0**: Initial release with basic CRM and quoting functionality

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## 🎯 **Roadmap**

### **Version 1.3** (Planned)
- Sales pipeline visualization
- Advanced reporting and analytics
- Email integration and automation
- Mobile application development

### **Future Versions**
- Multi-user support with role-based access
- Advanced AI features and predictive analytics
- Third-party integrations and API platform
- Enterprise-grade security and scalability

See [FUTURE_DEVELOPMENT_IDEAS.md](FUTURE_DEVELOPMENT_IDEAS.md) for comprehensive roadmap.

## 📞 **Support**

For support and questions:
- **Documentation**: Check the comprehensive documentation files
- **Issues**: Create an issue in the GitHub repository
- **Development**: See the development continuation guide

---

**CCS Quote Tool v1.2** - Empowering businesses with AI-driven customer relationship management and professional quoting capabilities.

**Last Updated**: October 9, 2025