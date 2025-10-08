# CCS Quote Tool - Version 1.0

A comprehensive lead generation and customer relationship management (CRM) system powered by GPT-5-mini AI, designed for IT service providers and cabling companies.

## 🚀 Features

### Lead Generation
- **AI-Powered Lead Discovery**: Uses GPT-5-mini with web search to find potential customers
- **Geographic Targeting**: Search by postcode and radius for localized leads
- **Business Type Filtering**: Focus on IT/MSP companies, cabling services, and related businesses
- **Real-time Campaign Processing**: Background processing ensures smooth user experience
- **Companies House Integration**: Automatic company data enrichment
- **LinkedIn Data Extraction**: Professional network information gathering

### Customer Management (CRM)
- **Lead to Customer Conversion**: Seamless conversion with data preservation
- **Contact Management**: Multiple contacts per customer with role-based organization
- **Business Intelligence**: AI-generated company analysis and opportunity assessment
- **Interaction Tracking**: Complete history of customer communications
- **Quote Management**: Integrated quoting system for proposals

### AI Analysis
- **Company Profiling**: Automated business intelligence generation
- **Technology Needs Assessment**: AI-predicted IT requirements
- **Competitor Analysis**: Market positioning insights
- **Opportunity Scoring**: Lead qualification and prioritization
- **Risk Assessment**: Business viability evaluation

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **AI Engine**: OpenAI GPT-5-mini with web search capabilities
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap)
- **External APIs**: 
  - OpenAI API (GPT-5-mini)
  - Companies House API
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
Flask-Login>=0.6.0
Flask-SQLAlchemy>=3.0.0
openai>=1.0.0
requests>=2.28.0
python-dotenv>=1.0.0
```

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ccs-quote-tool.git
   cd ccs-quote-tool
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   COMPANIES_HOUSE_API_KEY=your_companies_house_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Initialize database**
   ```bash
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## 📁 Project Structure

```
ccs-quote-tool/
├── app.py                          # Main Flask application
├── models.py                       # Core database models
├── models_crm.py                   # CRM-specific models
├── models_lead_generation.py       # Lead generation models
├── routes/
│   ├── main.py                     # Main routes
│   ├── auth.py                     # Authentication routes
│   ├── quotes.py                   # Quote management routes
│   ├── crm.py                      # CRM routes
│   └── lead_generation.py          # Lead generation routes
├── utils/
│   ├── lead_generation_service.py  # AI lead generation logic
│   ├── customer_intelligence.py    # AI analysis services
│   ├── external_data_service.py    # External API integrations
│   └── pricing_helper.py           # Pricing calculations
├── templates/
│   ├── base.html                   # Base template
│   ├── auth/                       # Authentication templates
│   ├── quotes/                     # Quote templates
│   ├── crm/                        # CRM templates
│   └── lead_generation/            # Lead generation templates
├── static/                         # Static assets (CSS, JS, images)
├── campaign_worker.py              # Background campaign processor
└── requirements.txt                # Python dependencies
```

## 🎯 Usage

### Creating Your First Campaign

1. **Navigate to Lead Generation**
   - Click "Lead Generation" in the sidebar
   - Click "Create New Campaign"

2. **Configure Campaign**
   - Enter campaign name and description
   - Set target postcode and search radius
   - Choose business type focus (IT/MSP, Cabling, etc.)
   - Set maximum results limit

3. **Run Campaign**
   - Click "Run Campaign"
   - Monitor progress in real-time
   - Campaign runs in background (3-5 minutes typical)

4. **Review Results**
   - View generated leads
   - Check AI analysis and scoring
   - Review company information and contacts

### Converting Leads to Customers

1. **Select Leads**
   - Use checkboxes to select multiple leads
   - Or convert individual leads

2. **Convert to CRM**
   - Click "Convert to Customer"
   - System automatically creates customer and contact records
   - Preserves all AI analysis and external data

3. **Manage Customers**
   - Navigate to CRM section
   - View customer profiles and interactions
   - Track follow-up activities

## 🔧 Configuration

### AI Settings
- **Model**: GPT-5-mini (configurable in API settings)
- **Token Limits**: 50,000 tokens for comprehensive analysis
- **Web Search**: Enabled for real-time business discovery
- **Temperature**: Default (GPT-5-mini optimized)

### Database Configuration
- **SQLite**: Default database with 30-second timeout
- **Connection Pooling**: Enabled for multi-threaded operations
- **Backup**: Regular database backups recommended

### External API Configuration
- **OpenAI API**: Required for AI lead generation
- **Companies House API**: Required for company data enrichment
- **Rate Limits**: Configured for optimal performance

## 🐛 Troubleshooting

### Common Issues

1. **Campaign Stuck in "Running" Status**
   - Check API key configuration
   - Verify internet connectivity
   - Review Flask application logs

2. **Database Lock Errors**
   - Restart the application
   - Check for concurrent database access
   - Verify file permissions

3. **AI Analysis Failures**
   - Verify OpenAI API key and credits
   - Check GPT-5-mini model availability
   - Review token usage limits

4. **Lead Conversion Errors**
   - Ensure all required fields are populated
   - Check business sector enum mappings
   - Verify contact information format

### Log Files
- Application logs: Console output
- Database logs: SQLite journal files
- API logs: OpenAI and external service responses

## 🔒 Security

- **Authentication**: Flask-Login session management
- **API Keys**: Environment variable storage
- **Database**: SQLite with connection security
- **Input Validation**: Comprehensive data sanitization
- **SQL Injection**: SQLAlchemy ORM protection

## 📊 Performance

- **Lead Generation**: 3-5 minutes per campaign (25 leads)
- **Database Operations**: <1 second for most queries
- **AI Analysis**: 30-60 seconds per company
- **Memory Usage**: ~100MB base, +50MB per active campaign

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review application logs for error details

## 🔄 Version History

### Version 1.0 (Current)
- Initial release with full lead generation capabilities
- GPT-5-mini AI integration with web search
- Complete CRM system with customer management
- Companies House and LinkedIn data integration
- Background processing for campaign management
- Comprehensive error handling and validation

---

**CCS Quote Tool v1.0** - Empowering IT service providers with AI-driven lead generation and customer management.