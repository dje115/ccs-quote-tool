import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app
from models import AIPrompt, db

DEFAULT_PROMPTS = [
    {
        'prompt_type': 'quote_analysis',
        'name': 'Structured Cabling Quotation Default',
        'description': 'Requests clarifications and produces a structured cabling quotation.',
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
       1. FIRST: Parse the project description carefully to extract ALL details (outlet counts, room dimensions, containment type, ceiling construction, etc.)
       2. Calculate total connections: Double outlets = 2 connections, Single outlets = 1 connection, Four-way outlets = 4 connections
       3. Identify any missing critical details (patch panel counts, testing & certification, rack power, etc.). Ask up to 5 short clarification questions.
       4. When sufficient information is available (or you must make reasonable assumptions), prepare a structured cabling quotation.
       
IMPORTANT CALCULATION RULES:
- Double outlets = 2 connections each (e.g., 20 double outlets = 40 connections)
- RJ45 connectors needed = number of connections (not outlets)
- Face plates needed = number of outlet locations (20 double + 4 single + 2 four-way = 26 face plates)
- Back boxes needed = number of outlet locations (one per face plate)
- Patch panels: each 24-port panel handles 24 connections (round up)
- Cable quantity: Estimate 25-30m average run length per outlet, add 10% waste, round up to full boxes
- CRITICAL: Cat5e/Cat6 copper cable has a 90m limit for data transmission
- CRITICAL: If cabinets/equipment are >90m apart, MUST use fiber optic cable for inter-building links
- Fiber materials needed: LC-LC multimode fiber cable, LC connectors, fiber patch panels, SFP modules
- Labour calculations: use hourly rate (day_rate ÷ 8 hours), not day rate directly
- Labour time: ~1.5 hours per double outlet, ~45 min per single outlet, ~2 hours per four-way outlet
- Roll testing time into installation time, don't show as separate line item
- Labour rounding: >8 hours = round up to next full day, 4-8 hours = half day, <4 hours = half day minimum
       
       EXAMPLE: "20 double + 4 single + 2 four-way outlets" = (20×2) + (4×1) + (2×4) = 52 total connections
       EXAMPLE: "40 twin + 4 quad + 10 twin outlets" = (40×2) + (4×4) + (10×2) = 80 + 16 + 20 = 116 total connections
       Cable needed: 116 outlets × 25m average × 1.1 waste factor = 3190m = 11 boxes of 305m cable

When you return the quotation you MUST respond in JSON with these keys:
- analysis (string)
- products (array). Each item must be an object with keys: item/name, quantity (number), notes (string).
- alternatives (array of objects with solution, pros, cons)
- estimated_time (number in hours)
- labour_breakdown (array of objects each with task, hours, engineer_count, day_rate, cost, notes)
- clarifications (array of outstanding clarification questions; return [] if none)
- quotation (object) containing:
    * client_requirement (string)
    * scope_of_works (array of bullet strings)
    * materials (array of objects with item, quantity, notes)
    * labour (object with engineers, hours, day_rate, total_cost, notes)
    * assumptions_exclusions (array of strings)

Always include every key even if you must supply an empty array/object. When making reasonable assumptions, mention them in notes or assumptions_exclusions.

If there is not enough information to calculate labour, return placeholder values but include the fields.

Example JSON structure (values illustrative):
{{
  "analysis": "Install 116 Cat5E connections (40 twin + 4 quad + 10 twin outlets) in two offices with 21U cabinets linked by fiber due to 200m distance",
  "products": [
    {{"item": "Cat5E Cable", "quantity": 11, "notes": "305m boxes for 116 connections (3190m total)"}},
    {{"item": "RJ45 Connectors", "quantity": 116, "notes": "For 116 connections"}},
    {{"item": "24-port Patch Panel", "quantity": 5, "notes": "5 panels for 116 connections"}},
    {{"item": "Face Plates", "quantity": 54, "notes": "Twin outlets (50) + Quad outlets (4)"}},
    {{"item": "Back Boxes", "quantity": 54, "notes": "One per outlet location"}},
    {{"item": "LC-LC Multimode Fiber Cable", "quantity": 1, "notes": "200m fiber link between cabinets (exceeds 90m copper limit)"}},
    {{"item": "LC Fiber Connectors", "quantity": 4, "notes": "2 pairs for cabinet link"}},
    {{"item": "Fiber Patch Panel", "quantity": 2, "notes": "One per cabinet for fiber termination"}},
    {{"item": "SFP Modules", "quantity": 2, "notes": "For switch fiber ports"}}
  ],
  "alternatives": [{{"solution": "Use Cat6a", "pros": "Future proof", "cons": "Higher cost"}}],
  "estimated_time": 42,
  "labour_breakdown": [{{"task": "Install outlets and testing", "hours": 87, "engineer_count": 2, "hourly_rate": 75, "cost": 13050, "notes": "Includes installation and testing for 116 connections across two offices"}}],
  "clarifications": ["Is out-of-hours access required?"],
  "quotation": {{
    "client_requirement": "Restated requirement...",
    "scope_of_works": ["Run Cat6 cabling via dado trunking", "Terminations and testing"],
    "materials": [
      {{"item": "Cat5E Cable", "quantity": 11, "notes": "305m boxes"}},
      {{"item": "RJ45 Connectors", "quantity": 116, "notes": "For all connections"}},
      {{"item": "24-port Patch Panel", "quantity": 5, "notes": "For 116 connections"}},
      {{"item": "Face Plates", "quantity": 54, "notes": "Various outlet types"}},
      {{"item": "Back Boxes", "quantity": 54, "notes": "One per outlet"}},
      {{"item": "LC-LC Multimode Fiber Cable", "quantity": 1, "notes": "200m inter-cabinet link"}},
      {{"item": "LC Fiber Connectors", "quantity": 4, "notes": "Fiber termination"}},
      {{"item": "Fiber Patch Panel", "quantity": 2, "notes": "Per cabinet"}},
      {{"item": "SFP Modules", "quantity": 2, "notes": "Switch fiber ports"}}
    ],
    "labour": {{"engineers": 2, "hours": 87, "hourly_rate": 75, "total_cost": 13050, "notes": "Includes installation and testing for 116 connections across two offices"}},
    "assumptions_exclusions": ["Client provides comms room power"]
  }},
  "travel_distance_km": 15.5,
  "travel_time_minutes": 32
}}

Return only JSON, no additional commentary.
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

    for prompt_data in DEFAULT_PROMPTS:
        prompt = AIPrompt(**prompt_data)
        db.session.add(prompt)

    db.session.commit()
    print('Default prompts created:', AIPrompt.query.count())
