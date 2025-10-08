#!/usr/bin/env python3
"""
Populate database with natural AI prompts that let the AI think freely like ChatGPT.
No restrictive rules - just let the AI analyze and provide intelligent responses.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import from app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app, db
from models import AIPrompt

# Natural prompts that let AI think freely
prompts_data = [
    {
        'prompt_type': 'quote_analysis',
        'name': 'Natural Project Analysis',
        'description': 'Natural AI analysis like ChatGPT - no restrictive rules, just intelligent project analysis',
        'system_prompt': (
            "You are a seasoned structured cabling contractor and estimator."
            " You produce practical, buildable quotations, highlight assumptions,"
            " and make sensible allowances for labour and materials."
        ),
        'user_prompt_template': """
You are a structured cabling contractor. The client has supplied the information below.

Project Title: {project_title}
Description: {project_description}
Building Type: {building_type}
Building Size: {building_size} sqm
Number of Floors: {number_of_floors}
Number of Rooms/Areas: {number_of_rooms}
Site Address: {site_address}

Solution Requirements:
- WiFi installation needed: {wifi_requirements}
- CCTV installation needed: {cctv_requirements}
- Door entry installation needed: {door_entry_requirements}
- Special requirements or constraints: {special_requirements}

Your tasks:
1. Analyze the project requirements and make reasonable assumptions for any missing details based on industry standards.
2. Prepare a complete structured cabling quotation that includes: client requirement restatement, scope of works, materials list, labour estimate, and assumptions/exclusions.

Response rules:
- Always respond in JSON format.
- When the caller is only requesting questions (questions_only mode) return: {{"clarifications": [..]}}.
- Otherwise return a JSON object with these keys:
  - analysis: concise narrative summary (string).
  - products: array of recommended products with item, quantity, unit_price, total_price, notes.
  - alternatives: array describing optional approaches with pros/cons.
  - estimated_time: total installation hours (number).
  - labour_breakdown: array of tasks with task, days, hours, day_rate, cost, notes.
  - clarifications: array of clarification questions (optional - only include if absolutely critical).
  - quotation: object with client_requirement, scope_of_works, materials, labour, assumptions_exclusions.

If details are missing, state the reasonable assumption you are making inside the quotation sections. Provide a complete quotation with all pricing and details.
""",
        'variables': json.dumps(["project_title", "project_description", "building_type", "building_size", "number_of_floors", "number_of_rooms", "site_address", "wifi_requirements", "cctv_requirements", "door_entry_requirements", "special_requirements"]),
        'is_default': True,
        'is_active': True
    }
]


with app.app_context():
    print('Clearing existing prompts...')
    AIPrompt.query.delete()
    db.session.commit()
    
    print('Creating natural prompts...')
    for prompt_data in prompts_data:
        prompt = AIPrompt(**prompt_data)
        db.session.add(prompt)
    
    db.session.commit()
    print(f'Natural prompts created: {len(prompts_data)}')
