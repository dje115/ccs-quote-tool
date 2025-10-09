#!/usr/bin/env python3
"""
CRM models for customer and contact management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import json
import enum

# Import the existing db instance
from models import db

class BusinessSector(enum.Enum):
    """Business sector enumeration"""
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    HOSPITALITY = "hospitality"
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    GOVERNMENT = "government"
    OTHER = "other"

class CustomerStatus(enum.Enum):
    """Customer status enumeration"""
    LEAD = "lead"
    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FORMER = "former"

class ContactRole(enum.Enum):
    """Contact role enumeration"""
    DECISION_MAKER = "decision_maker"
    TECHNICAL = "technical"
    FINANCE = "finance"
    FACILITIES = "facilities"
    IT_MANAGER = "it_manager"
    GENERAL = "general"

class Customer(db.Model):
    """Customer/Company model"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String(200), nullable=False)
    business_sector = Column(Enum(BusinessSector), nullable=True)
    company_registration = Column(String(50), nullable=True)  # Company registration number
    registration_confirmed = Column(Boolean, default=False)  # Human confirmation of registration
    vat_number = Column(String(50), nullable=True)
    
    # Business Intelligence (AI-generated)
    estimated_employees = Column(Integer, nullable=True)
    estimated_revenue = Column(String(50), nullable=True)  # e.g., "£1M-£5M"
    business_size_category = Column(String(50), nullable=True)  # e.g., "Small", "Medium", "Large"
    primary_business_activities = Column(Text, nullable=True)
    technology_maturity = Column(String(50), nullable=True)  # e.g., "Basic", "Advanced", "Enterprise"
    it_budget_estimate = Column(String(50), nullable=True)  # e.g., "£10K-£50K annually"
    growth_potential = Column(String(50), nullable=True)  # e.g., "High", "Medium", "Low"
    
    # Contact Information
    website = Column(String(255), nullable=True)
    main_phone = Column(String(50), nullable=True)
    main_email = Column(String(120), nullable=True)
    
    # Address Information
    billing_address = Column(Text, nullable=True)
    billing_postcode = Column(String(20), nullable=True)
    shipping_address = Column(Text, nullable=True)
    shipping_postcode = Column(String(20), nullable=True)
    
    # CRM Fields
    status = Column(Enum(CustomerStatus), default=CustomerStatus.PROSPECT)
    source = Column(String(100), nullable=True)  # How they found you
    lead_score = Column(Integer, default=0)  # 0-100 lead scoring
    last_contact_date = Column(DateTime, nullable=True)
    next_follow_up = Column(DateTime, nullable=True)
    
    # AI-Generated Intelligence
    ai_company_profile = Column(Text, nullable=True)  # AI-generated company summary
    ai_technology_needs = Column(Text, nullable=True)  # AI-predicted technology needs
    ai_competitors = Column(Text, nullable=True)  # AI-identified competitors
    ai_opportunities = Column(Text, nullable=True)  # AI-identified opportunities
    ai_risks = Column(Text, nullable=True)  # AI-identified risks
    ai_analysis_raw = Column(Text, nullable=True)  # Complete AI analysis as JSON
    
    # External Data Sources
    linkedin_url = Column(String(255), nullable=True)
    linkedin_data = Column(Text, nullable=True)  # LinkedIn data as JSON
    companies_house_data = Column(Text, nullable=True)  # Companies House data as JSON
    google_maps_data = Column(Text, nullable=True)      # Google Maps location data as JSON
    website_data = Column(Text, nullable=True)  # Website scraping data as JSON
    
    # Address management
    excluded_addresses = Column(Text, nullable=True)  # JSON array of excluded address IDs/names
    manual_addresses = Column(Text, nullable=True)    # JSON array of manually added addresses
    
    # AI-Generated Address Analysis
    primary_address = Column(Text, nullable=True)  # AI-detected primary business address
    additional_sites = Column(Text, nullable=True)  # AI-detected additional locations
    location_analysis = Column(Text, nullable=True)  # AI analysis of geographic spread
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    # Relationships
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="customer")
    interactions = relationship("CustomerInteraction", back_populates="customer", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert customer to dictionary"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'business_sector': self.business_sector.value if self.business_sector else None,
            'company_registration': self.company_registration,
            'vat_number': self.vat_number,
            'estimated_employees': self.estimated_employees,
            'estimated_revenue': self.estimated_revenue,
            'business_size_category': self.business_size_category,
            'primary_business_activities': self.primary_business_activities,
            'technology_maturity': self.technology_maturity,
            'it_budget_estimate': self.it_budget_estimate,
            'growth_potential': self.growth_potential,
            'website': self.website,
            'main_phone': self.main_phone,
            'main_email': self.main_email,
            'billing_address': self.billing_address,
            'billing_postcode': self.billing_postcode,
            'shipping_address': self.shipping_address,
            'shipping_postcode': self.shipping_postcode,
            'status': self.status.value if self.status else None,
            'source': self.source,
            'lead_score': self.lead_score,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'next_follow_up': self.next_follow_up.isoformat() if self.next_follow_up else None,
            'ai_company_profile': self.ai_company_profile,
            'ai_technology_needs': self.ai_technology_needs,
            'ai_competitors': self.ai_competitors,
            'ai_opportunities': self.ai_opportunities,
            'ai_risks': self.ai_risks,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'contact_count': len(self.contacts),
            'quote_count': len(self.quotes),
            'total_quote_value': sum(q.estimated_cost for q in self.quotes if q.estimated_cost)
        }

class Contact(db.Model):
    """Contact model - multiple contacts per customer"""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    role = Column(Enum(ContactRole), default=ContactRole.GENERAL)
    
    # Contact Information - Primary fields for backward compatibility
    email = Column(String(120), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Additional contact information
    email_secondary = Column(String(120), nullable=True)
    phone_secondary = Column(String(50), nullable=True)
    
    # Primary contact designations
    primary_email = Column(String(20), default='primary')  # 'primary' or 'secondary'
    primary_phone = Column(String(20), default='primary')  # 'primary' or 'secondary'
    
    # Preferences
    preferred_contact_method = Column(String(20), nullable=True)  # email, phone, mobile
    preferred_contact_time = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="contacts")
    interactions = relationship("CustomerInteraction", back_populates="contact", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert contact to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'job_title': self.job_title,
            'department': self.department,
            'role': self.role.value if self.role else None,
            'email': self.email,
            'phone': self.phone,
            'mobile': self.mobile,
            'preferred_contact_method': self.preferred_contact_method,
            'preferred_contact_time': self.preferred_contact_time,
            'notes': self.notes,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CustomerInteraction(db.Model):
    """Customer interaction/activity log"""
    __tablename__ = 'customer_interactions'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=True)
    
    # Interaction Details
    interaction_type = Column(String(50), nullable=False)  # call, email, meeting, quote_sent, etc.
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    outcome = Column(String(100), nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    
    # Metadata
    interaction_date = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="interactions")
    contact = relationship("Contact", back_populates="interactions")
    
    def to_dict(self):
        """Convert interaction to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'contact_id': self.contact_id,
            'contact_name': self.contact.full_name if self.contact else None,
            'interaction_type': self.interaction_type,
            'subject': self.subject,
            'description': self.description,
            'outcome': self.outcome,
            'follow_up_required': self.follow_up_required,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'interaction_date': self.interaction_date.isoformat(),
            'created_at': self.created_at.isoformat()
        }

# Note: Customer relationship with Quote is defined in models.py to avoid circular imports
