#!/usr/bin/env python3
"""
Populate database with flexible AI prompts that can handle any type of project.
Less restrictive, more intelligent analysis based on actual project requirements.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import from app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app, db
from models import AIPrompt

# Flexible prompts that adapt to any project type
prompts_data = [
    {
        'prompt_type': 'quote_analysis',
        'name': 'Flexible Project Analysis',
        'description': 'Intelligent analysis that adapts to any project type (WiFi, CCTV, door entry, cabling, etc.)',
        'system_prompt': (
            "You are an experienced IT and communications contractor with expertise in: "
            "- Structured cabling (Cat5e/Cat6/Cat6a/fiber) "
            "- WiFi networks and access points "
            "- CCTV surveillance systems "
            "- Door entry and access control "
            "- Network infrastructure and equipment "
            "Analyze each project based on its actual requirements. Don't assume project types - read the description carefully. "
            "Provide specific product recommendations with pricing when possible. Calculate realistic material quantities "
            "and labour requirements based on what is actually being requested."
        ),
        'user_prompt_template': """
Analyze this project and create a comprehensive quotation. Read the project description carefully and identify what is actually being requested.

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

**Labour Rate:** £300 per pair of engineers per day (8-hour day)

**Analysis Instructions:**
1. READ THE PROJECT DESCRIPTION CAREFULLY - don't make assumptions
2. Identify what is actually being requested (WiFi, CCTV, door entry, cabling, or combination)
3. Calculate materials and labour based on the actual requirements
4. Recommend specific products with pricing when possible
5. Ask clarification questions if critical details are missing
6. Consider all technical requirements and constraints

**For Different Project Types:**
- **WiFi Projects**: Include access points, controllers, cabling, power requirements
- **CCTV Projects**: Include cameras, recorders, monitors, cabling, storage
- **Door Entry Projects**: Include access control, readers, locks, cabling, software
- **Structured Cabling**: Include cables, connectors, face plates, patch panels, cabinets
- **Combined Projects**: Include all relevant systems and their integration

**Technical Guidelines:**
- For structured cabling: Twin outlets = 2 connections, Quad outlets = 4 connections
- For WiFi: Consider coverage areas, access point placement, cabling requirements
- For CCTV: Consider camera types, recording requirements, storage needs
- For door entry: Consider access points, user management, integration needs
- Always consider distance limits for copper cabling (100m) and recommend fiber for longer runs
- Include all necessary materials: cables, connectors, face plates, back boxes, patch panels, equipment, etc.

**Return comprehensive JSON with ALL relevant information:**

{{
  "analysis": "Detailed analysis of what the project actually involves",
  "products": [
    {{"item": "Specific product name", "quantity": 1, "unit_price": 0, "total_price": 0, "notes": "Detailed reasoning and specifications"}}
  ],
  "alternatives": [
    {{"solution": "Alternative approach", "pros": "Benefits", "cons": "Drawbacks", "cost_difference": "Higher/lower/same"}}
  ],
  "estimated_time": 0,
  "labour_breakdown": [
    {{"task": "Specific task description", "days": 0, "engineer_count": 2, "day_rate": 300, "cost": 0, "notes": "Task details and reasoning"}}
  ],
  "clarifications": ["Questions about missing critical details"],
  "quotation": {{
    "client_requirement": "Clear restatement of what the client actually wants",
    "scope_of_works": ["Detailed list of work items based on actual requirements"],
    "materials": [
      {{"item": "Material name", "quantity": 1, "unit_price": 0, "total_price": 0, "notes": "Specifications and reasoning"}}
    ],
    "labour": {{"engineers": 2, "days": 0, "day_rate": 300, "total_cost": 0, "notes": "Labour breakdown details"}},
    "assumptions_exclusions": ["All assumptions made and items excluded"]
  }},
  "travel_distance_miles": 0,
  "travel_time_minutes": 0
}}

**Important:** Include pricing information wherever possible. If you know typical prices for products, include them. If not, leave as 0 but note that pricing needs to be sourced.
""",
        'variables': json.dumps(["project_title", "project_description", "building_type", "building_size", "number_of_floors", "number_of_rooms", "site_address", "wifi_requirements", "cctv_requirements", "door_entry_requirements", "special_requirements"]),
        'is_default': True,
        'is_active': True
    },
    {
        'prompt_type': 'product_search',
        'name': 'Enhanced Product Search',
        'description': 'Search for products with pricing information across all categories.',
        'system_prompt': "You are a product expert for IT and communications equipment. Provide detailed product recommendations with specifications and pricing information.",
        'user_prompt_template': "Search for {category} products related to: {query}\n\nProvide specific products with:\n- Product name and model\n- Detailed specifications\n- Typical use case\n- Current market price range\n- Availability\n\nFormat as JSON array with pricing information.",
        'variables': json.dumps(["category", "query"]),
        'is_default': True,
        'is_active': True
    },
    {
        'prompt_type': 'building_analysis',
        'name': 'Comprehensive Building Analysis',
        'description': 'Analyzes building information for any type of IT/communications project.',
        'system_prompt': "You are a building analysis expert specializing in IT and communications installations. Analyze building information and provide technical insights for various project types.",
        'user_prompt_template': "Analyze this building for IT/communications requirements:\n\nAddress: {address}\nBuilding Type: {building_type}\nSize: {building_size} sqm\n\nProvide recommendations for:\n- Cable routing strategies\n- Equipment placement locations\n- Power requirements\n- Access considerations\n- Potential challenges\n- Suitable technologies\n\nConsider all types of installations: WiFi, CCTV, door entry, structured cabling, network infrastructure.",
        'variables': json.dumps(["address", "building_type", "building_size"]),
        'is_default': True,
        'is_active': True
    }
]


with app.app_context():
    print('Clearing existing prompts...')
    AIPrompt.query.delete()
    db.session.commit()
    
    print('Creating flexible prompts...')
    for prompt_data in prompts_data:
        prompt = AIPrompt(**prompt_data)
        db.session.add(prompt)
    
    db.session.commit()
    print(f'Flexible prompts created: {len(prompts_data)}')


