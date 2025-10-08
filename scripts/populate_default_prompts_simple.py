#!/usr/bin/env python3
"""
Populate database with simplified AI prompts for structured cabling quotations.
Based on ChatGPT's natural approach - just give the day rate and ask for structured JSON.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import from app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app, db
from models import AIPrompt

# Clear existing prompts and create new simplified ones
prompts_data = [
    {
        'prompt_type': 'quote_analysis',
        'name': 'Simplified Quote Analysis',
        'description': 'Simple, natural prompt that gives day rate and asks for structured JSON output',
        'system_prompt': (
            "You are an experienced IT and communications contractor specializing in structured cabling, "
            "WiFi, CCTV, door entry systems, and network infrastructure. Analyze the project requirements "
            "carefully and provide professional quotations with accurate calculations, realistic material "
            "quantities, and specific product recommendations with pricing where possible. Consider technical "
            "constraints like distance limits for copper cabling (100m) and recommend appropriate solutions."
        ),
        'user_prompt_template': """
You are an experienced structured cabling contractor. Create a professional quotation for this project.

**Project Details:**
Project Title: {project_title}
Description: {project_description}
Building Type: {building_type}
Building Size: {building_size} sqm
Number of Floors: {number_of_floors}
Number of Rooms/Areas: {number_of_rooms}
Site Address: {site_address}

**Requirements:**
- WiFi installation: {wifi_requirements}
- CCTV installation: {cctv_requirements}
- Door entry installation: {door_entry_requirements}
- Special requirements: {special_requirements}

**Labour Rounding Rules:**
- Less than 8 hours: round up to nearest half day (0.5 days)
- 8 hours or more: round up to nearest full day
- Always calculate in days, not hours
- Use the day rate provided above for calculations

**Connection Calculation Rules:**
- Twin outlets = 2 connections each
- Quad outlets = 4 connections each
- Example: "40 twin + 4 quad + 10 twin" = (40×2) + (4×4) + (10×2) = 80 + 16 + 20 = 116 total connections

**Material Requirements:**
- RJ45 connectors = total number of connections (not outlets)
- Face plates = number of outlet locations (40 twin + 4 quad + 10 twin = 54 face plates)
- Back boxes = number of outlet locations (one per face plate)
- Patch panels = total connections ÷ 24 (round up)
- Cable = estimate 25-30m per outlet + 10% waste, round up to full boxes
- Always include face plates and back boxes in materials list

**Preferred Brands:**
- Cabling: Connectix
- CCTV: Unifi
- Door Entry: Paxton Net2
- WiFi: Unifi

Please provide a structured cabling quotation in JSON format with the following structure:

{{
  "analysis": "Brief summary of the project scope and approach",
  "products": [
    {{"item": "Cat5e Cable", "quantity": 4, "notes": "305m boxes for 116 connections"}},
    {{"item": "RJ45 Connectors", "quantity": 116, "notes": "For all connections"}},
    {{"item": "24-port Patch Panel", "quantity": 5, "notes": "For 116 connections"}},
    {{"item": "Face Plates", "quantity": 54, "notes": "For all outlet locations"}},
    {{"item": "Back Boxes", "quantity": 54, "notes": "One per outlet location"}},
    {{"item": "Fiber Cable", "quantity": 1, "notes": "200m for cabinet link"}}
  ],
  "alternatives": [
    {{"solution": "Alternative approach", "pros": "Benefits", "cons": "Drawbacks"}}
  ],
  "estimated_time": 5,
  "labour_breakdown": [
    {{"task": "Install outlets and cabinets", "days": 3, "engineer_count": 2, "day_rate": "[use day rate from settings]", "cost": "[3 days × day rate]", "notes": "For 116 connections across two offices"}},
    {{"task": "Fiber link installation", "days": 2, "engineer_count": 2, "day_rate": "[use day rate from settings]", "cost": "[2 days × day rate]", "notes": "200m fiber link between cabinets"}}
  ],
  "clarifications": ["Any questions you need answered"],
  "quotation": {{
    "client_requirement": "Restated client requirement",
    "scope_of_works": ["List of work items"],
    "materials": [
      {{"item": "Cat5e Cable", "quantity": 4, "notes": "305m boxes"}},
      {{"item": "RJ45 Connectors", "quantity": 116, "notes": "For all connections"}},
      {{"item": "24-port Patch Panel", "quantity": 5, "notes": "For connections"}},
      {{"item": "Face Plates", "quantity": 54, "notes": "For outlet locations"}},
      {{"item": "Back Boxes", "quantity": 54, "notes": "One per outlet"}},
      {{"item": "Fiber Cable", "quantity": 1, "notes": "200m cabinet link"}}
    ],
    "labour": {{"engineers": 2, "days": 5, "day_rate": "[use day rate from settings]", "total_cost": "[5 days × day rate]", "notes": "Total for pair of engineers over 5 days"}},
    "assumptions_exclusions": ["Assumptions and exclusions"]
  }},
  "travel_distance_miles": 9.6,
  "travel_time_minutes": 32
}}

Always include every key in the JSON response. Make reasonable assumptions and mention them in notes or assumptions_exclusions.
""",
        'variables': json.dumps(["project_title", "project_description", "building_type", "building_size", "number_of_floors", "number_of_rooms", "site_address", "wifi_requirements", "cctv_requirements", "door_entry_requirements", "special_requirements"]),
        'is_default': True,
        'is_active': True
    },
    {
        'prompt_type': 'product_search',
        'name': 'Default Product Search',
        'description': 'Searches for networking products and returns structured results.',
        'system_prompt': "You are a product expert for structured cabling, networking, and security equipment. Provide accurate product recommendations.",
        'user_prompt_template': "Search for {category} products related to: {query}\n\nProvide a list of specific products with:\n- Product name and model\n- Brief description\n- Typical use case\n- Estimated price range\n\nFormat as JSON array of objects.",
        'variables': json.dumps(["category", "query"]),
        'is_default': True,
        'is_active': True
    },
    {
        'prompt_type': 'building_analysis',
        'name': 'Default Building Analysis',
        'description': 'Analyses building information for cabling projects.',
        'system_prompt': "You are a building analysis expert specializing in structured cabling installations. Analyze building information and provide technical insights for cabling projects.",
        'user_prompt_template': "Analyze this building for structured cabling requirements:\n\nAddress: {address}\nBuilding Type: {building_type}\nSize: {building_size} sqm\n\nProvide recommendations for:\n- Cable routing strategies\n- Equipment placement locations\n- Power requirements\n- Access considerations\n- Potential challenges",
        'variables': json.dumps(["address", "building_type", "building_size"]),
        'is_default': True,
        'is_active': True
    }
]


with app.app_context():
    print('Clearing existing prompts...')
    AIPrompt.query.delete()
    db.session.commit()
    
    print('Creating simplified prompts...')
    for prompt_data in prompts_data:
        prompt = AIPrompt(**prompt_data)
        db.session.add(prompt)
    
    db.session.commit()
    print(f'Simplified prompts created: {len(prompts_data)}')
