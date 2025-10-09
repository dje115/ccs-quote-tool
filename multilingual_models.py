#!/usr/bin/env python3
"""
Database models updates for multilingual support
"""

# Add to models.py or models_crm.py:

user_language_model = '''
# Add to User model:
class User(db.Model):
    # ... existing fields ...
    language = Column(String(10), default='en')  # Store user's preferred language
    timezone = Column(String(50), default='UTC')  # Store user's timezone

# Add to Customer model:
class Customer(db.Model):
    # ... existing fields ...
    language = Column(String(10), default='en')  # Customer's preferred language
    currency = Column(String(3), default='GBP')  # Customer's preferred currency
'''

print("Database model updates for multilingual support:")
print(user_language_model)
