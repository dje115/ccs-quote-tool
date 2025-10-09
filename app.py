from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ccs_quotes.db?timeout=30'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'timeout': 30,  # 30 second timeout for database operations
        'check_same_thread': False  # Allow multi-threading
    }
}

# Add JSON filter for templates
@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return None

# Add dict filter for templates to exclude specific keys
@app.template_filter('dict_filter')
def dict_filter_filter(dict_obj, exclude_key):
    """Filter out a specific key from a dictionary"""
    if not dict_obj:
        return {}
    return {k: v for k, v in dict_obj.items() if k != exclude_key}

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'

# Import models and initialize db
from models import db, User, Quote, PricingItem, Template, APISettings, AIPrompt
from models_lead_generation import LeadGenerationCampaign, Lead, LeadGenerationPrompt, LeadInteraction
db.init_app(app)

# Import routes and utilities
from routes.main import main_bp
from routes.api import api_bp
from routes.api_simple import api_simple_bp
from routes.admin import admin_bp
from routes.consistency import consistency_bp
from routes.crm import crm_bp
from routes.lead_generation import lead_generation_bp
from utils.ai_helper import AIHelper
from utils.pricing_helper import PricingHelper
from utils.document_generator import DocumentGenerator

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(api_simple_bp, url_prefix='/api-simple')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(consistency_bp)
app.register_blueprint(crm_bp, url_prefix='/crm')
app.register_blueprint(lead_generation_bp, url_prefix='/lead-generation')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Initialize helpers (these will initialize when needed, not at startup)
ai_helper = None
pricing_helper = None
doc_generator = None

def init_helpers():
    global ai_helper, pricing_helper, doc_generator
    if ai_helper is None:
        ai_helper = AIHelper()
    if pricing_helper is None:
        pricing_helper = PricingHelper()
    if doc_generator is None:
        doc_generator = DocumentGenerator()

# Create tables and initialize
with app.app_context():
    db.create_all()
    
    # Create default admin user if none exists
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@ccs.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
    
    # Don't initialize helpers at startup to avoid proxy errors
    # They will be initialized when actually needed

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
