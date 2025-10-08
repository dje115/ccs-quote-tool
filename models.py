from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120), nullable=True)
    client_phone = db.Column(db.String(20), nullable=True)
    project_title = db.Column(db.String(200), nullable=False)
    project_description = db.Column(db.Text, nullable=True)
    site_address = db.Column(db.Text, nullable=False)
    building_type = db.Column(db.String(100), nullable=True)
    building_size = db.Column(db.Float, nullable=True)  # in square meters
    number_of_floors = db.Column(db.Integer, default=1)
    number_of_rooms = db.Column(db.Integer, default=1)
    cabling_type = db.Column(db.String(50), nullable=True)  # cat5e, cat6, fiber
    wifi_requirements = db.Column(db.Boolean, default=False)
    cctv_requirements = db.Column(db.Boolean, default=False)
    door_entry_requirements = db.Column(db.Boolean, default=False)
    special_requirements = db.Column(db.Text, nullable=True)
    
    # AI-generated content
    ai_analysis = db.Column(db.Text, nullable=True)
    recommended_products = db.Column(db.Text, nullable=True)  # JSON string
    estimated_time = db.Column(db.Integer, nullable=True)  # hours
    estimated_cost = db.Column(db.Float, nullable=True)
    alternative_solutions = db.Column(db.Text, nullable=True)  # JSON string
    clarifications_log = db.Column(db.Text, nullable=True)  # JSON array of {question, answer}
    ai_raw_response = db.Column(db.Text, nullable=True)  # Complete raw AI response for debugging/reference
    
    # Quote details
    quote_data = db.Column(db.Text, nullable=True)  # JSON string with full quote details
    labour_breakdown = db.Column(db.Text, nullable=True)  # JSON array of labour items
    quotation_details = db.Column(db.Text, nullable=True)  # JSON object with structured quotation sections
    travel_distance_km = db.Column(db.Float, nullable=True)
    travel_time_minutes = db.Column(db.Float, nullable=True)
    company_name = db.Column(db.String(200), nullable=True)
    company_address = db.Column(db.Text, nullable=True)
    company_postcode = db.Column(db.String(20), nullable=True)
    travel_time_hours = db.Column(db.Float, nullable=True)
    travel_cost = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, sent, accepted, declined
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref=db.backref('quotes', lazy=True))

class PricingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)  # cabling, wifi, cctv, door_entry
    subcategory = db.Column(db.String(100), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    unit = db.Column(db.String(20), nullable=False)  # meter, piece, hour, etc.
    cost_per_unit = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100), nullable=True)
    part_number = db.Column(db.String(100), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = db.Column(db.String(50), default='manual')  # manual, api, excel

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template_type = db.Column(db.String(50), nullable=False)  # quote, email
    content = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text, nullable=True)  # JSON string of available variables
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APISettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(50), unique=True, nullable=False)  # openai, google_maps
    api_key = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    suppliers = db.relationship('Supplier', backref='category', lazy=True)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    pricing_url = db.Column(db.String(500), nullable=True)  # Specific URL for pricing API or page
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_preferred = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    api_key = db.Column(db.String(200), nullable=True)  # For API-based pricing
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pricing_items = db.relationship('SupplierPricing', backref='supplier', lazy=True)

class SupplierPricing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_code = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='GBP')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class AIPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_type = db.Column(db.String(50), nullable=False)  # quote_analysis, product_search, building_analysis
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    system_prompt = db.Column(db.Text, nullable=False)
    user_prompt_template = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text, nullable=True)  # JSON string of available variables
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIPromptHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey('ai_prompt.id'), nullable=True)
    prompt_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    system_prompt = db.Column(db.Text, nullable=False)
    user_prompt_template = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text, nullable=True)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prompt = db.relationship('AIPrompt', backref=db.backref('history', lazy='dynamic'))

# Import CRM models
from models_crm import Customer, Contact, CustomerInteraction

# Add customer relationship to Quote model
Quote.customer = db.relationship('Customer', back_populates='quotes')