#!/usr/bin/env python3
"""
AI-Powered Translation Strategy
"""

ai_translation_approach = '''
# AI Translation Implementation

## 1. On-Demand Translation (Recommended)
Instead of pre-translating everything, translate on-demand:

```python
def translate_text(text, target_language, context="general"):
    """Translate text using GPT-5"""
    prompt = f"""
    Translate the following {context} text to {target_language}.
    Maintain professional business tone.
    Keep technical terms consistent.
    
    Text: {text}
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=1000
    )
    
    return response.choices[0].message.content
```

## 2. Caching Strategy
```python
# Cache translations in database
class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_text = db.Column(db.Text)
    translated_text = db.Column(db.Text)
    target_language = db.Column(db.String(10))
    context = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## 3. Template Integration
```python
# Custom template filter
@app.template_filter('translate')
def translate_filter(text, lang=None):
    if not lang or lang == 'en':
        return text
    
    # Check cache first
    cached = Translation.query.filter_by(
        original_text=text, 
        target_language=lang
    ).first()
    
    if cached:
        return cached.translated_text
    
    # Translate with AI
    translated = translate_text(text, lang)
    
    # Cache result
    translation = Translation(
        original_text=text,
        translated_text=translated,
        target_language=lang
    )
    db.session.add(translation)
    db.session.commit()
    
    return translated
```

## 4. Template Usage
```html
<!-- Simple translation -->
<h1>{{ "Lead Generation Dashboard" | translate(user.language) }}</h1>

<!-- With context -->
<p>{{ "Welcome to your dashboard" | translate(user.language, "greeting") }}</p>

<!-- Enum translation -->
<span>{{ _(customer.status.value) | translate(user.language, "status") }}</span>
```
'''

print("AI Translation Strategy:")
print(ai_translation_approach)
