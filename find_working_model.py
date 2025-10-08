#!/usr/bin/env python3
"""
Find which GPT model actually works
"""
import sys
sys.path.insert(0, '.')

from app import app
from models import APISettings

with app.app_context():
    # Get API key
    openai_setting = APISettings.query.filter_by(service_name='openai').first()
    
    if not openai_setting or not openai_setting.api_key:
        print("❌ No OpenAI API key found in database")
        exit(1)
    
    print(f"API Key: {openai_setting.api_key[:10]}...{openai_setting.api_key[-4:]}\n")
    
    from openai import OpenAI
    client = OpenAI(api_key=openai_setting.api_key, timeout=30.0)
    
    # Try different models
    models_to_test = [
        "gpt-5",
        "gpt-4o", 
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo"
    ]
    
    for model in models_to_test:
        print(f"Testing {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello from " + model + "!'"}
                ],
                max_completion_tokens=50,
                timeout=10.0
            )
            
            result = response.choices[0].message.content
            if result and len(result) > 0:
                print(f"  ✅ {model}: {result}")
            else:
                print(f"  ⚠️  {model}: Empty response")
                
        except Exception as e:
            print(f"  ❌ {model}: {str(e)[:100]}")
        
        print()


