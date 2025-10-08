#!/usr/bin/env python3
"""
Database models for lead generation system
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Float, JSON

# Import the existing db instance
from models import db

class LeadGenerationStatus(enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"

class LeadSource(enum.Enum):
    AI_GENERATED = "ai_generated"
    MANUAL_ENTRY = "manual_entry"
    IMPORT = "import"
    REFERRAL = "referral"

class LeadGenerationCampaign(db.Model):
    __tablename__ = 'lead_generation_campaigns'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prompt_type = Column(String(100), nullable=False)  # e.g., 'it_msp_expansion', 'custom'
    custom_prompt = Column(Text, nullable=True)
    postcode = Column(String(20), nullable=False)
    distance_miles = Column(Integer, default=20)
    max_results = Column(Integer, default=100)
    company_name_filter = Column(String(255), nullable=True)  # For "similar to" searches
    
    # Campaign settings
    include_existing_customers = Column(Boolean, default=False)
    exclude_duplicates = Column(Boolean, default=True)
    minimum_company_size = Column(Integer, nullable=True)
    business_sectors = Column(JSON, nullable=True)  # Array of business sectors to focus on
    
    # Status and tracking
    status = Column(Enum(LeadGenerationStatus), default=LeadGenerationStatus.DRAFT)
    total_found = Column(Integer, default=0)
    leads_created = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # AI analysis results
    ai_analysis_summary = Column(Text, nullable=True)
    search_criteria_used = Column(JSON, nullable=True)
    data_sources_used = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Relationships
    leads = db.relationship('Lead', backref='campaign', lazy=True, cascade="all, delete-orphan")

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('lead_generation_campaigns.id'), nullable=False)
    
    # Company information
    company_name = Column(String(255), nullable=False)
    website = Column(String(255), nullable=True)
    company_registration = Column(String(50), nullable=True)
    registration_confirmed = Column(Boolean, default=False)
    
    # Contact information
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(120), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_title = Column(String(100), nullable=True)
    
    # Address information
    address = Column(Text, nullable=True)
    postcode = Column(String(20), nullable=True)
    distance_from_search_center = Column(Float, nullable=True)  # in miles
    
    # Business information
    business_sector = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)  # e.g., "10-50 employees"
    annual_revenue = Column(String(50), nullable=True)
    
    # Lead scoring and qualification
    lead_score = Column(Integer, default=0)  # 0-100
    qualification_reason = Column(Text, nullable=True)
    potential_project_value = Column(Float, nullable=True)
    timeline_estimate = Column(String(100), nullable=True)  # e.g., "Q1 2024", "Within 6 months"
    
    # AI analysis
    ai_analysis = Column(JSON, nullable=True)
    ai_confidence_score = Column(Float, nullable=True)  # 0.0-1.0
    ai_recommendation = Column(Text, nullable=True)
    ai_notes = Column(Text, nullable=True)
    
    # Status and tracking
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    source = Column(Enum(LeadSource), default=LeadSource.AI_GENERATED)
    
    # Conversion tracking
    converted_to_customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    conversion_date = Column(DateTime, nullable=True)
    conversion_value = Column(Float, nullable=True)
    
    # External data sources
    linkedin_url = Column(String(255), nullable=True)
    linkedin_data = Column(JSON, nullable=True)
    companies_house_data = Column(JSON, nullable=True)
    website_data = Column(JSON, nullable=True)
    social_media_links = Column(JSON, nullable=True)
    
    # Notes and follow-up
    notes = Column(Text, nullable=True)
    last_contact_date = Column(DateTime, nullable=True)
    next_follow_up_date = Column(DateTime, nullable=True)
    contact_attempts = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Relationships
    interactions = db.relationship('LeadInteraction', backref='lead', lazy=True, cascade="all, delete-orphan")

class LeadInteraction(db.Model):
    __tablename__ = 'lead_interactions'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False)
    
    interaction_type = Column(String(50), nullable=False)  # e.g., 'call', 'email', 'meeting', 'quote_sent'
    subject = Column(String(255), nullable=True)
    summary = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Outcome tracking
    outcome = Column(String(100), nullable=True)  # e.g., 'positive', 'negative', 'neutral', 'no_response'
    next_steps = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)

class LeadGenerationPrompt(db.Model):
    __tablename__ = 'lead_generation_prompts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prompt_type = Column(String(100), nullable=False)  # e.g., 'it_msp_expansion', 'education', 'custom'
    prompt_template = Column(Text, nullable=False)
    
    # Prompt configuration
    requires_postcode = Column(Boolean, default=True)
    requires_distance = Column(Boolean, default=True)
    requires_company_name = Column(Boolean, default=False)
    max_results_default = Column(Integer, default=100)
    
    # AI settings
    ai_model = Column(String(50), default='gpt-4o-mini')
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4000)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)

