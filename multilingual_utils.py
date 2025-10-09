#!/usr/bin/env python3
"""
Utility functions for multilingual support
"""

# utils/i18n_utils.py:

i18n_utils = '''
# utils/i18n_utils.py
from flask import current_app
from flask_babel import get_locale, format_currency, format_datetime, format_number
from datetime import datetime
import pytz

def get_user_timezone(user):
    """Get user's timezone or default to UTC"""
    if user and hasattr(user, 'timezone'):
        return pytz.timezone(user.timezone)
    return pytz.UTC

def format_currency_localized(amount, currency='GBP', user=None):
    """Format currency based on user's locale"""
    locale = get_locale()
    return format_currency(amount, currency, locale=locale)

def format_datetime_localized(dt, user=None, format='medium'):
    """Format datetime based on user's locale and timezone"""
    if not dt:
        return ''
    
    locale = get_locale()
    user_tz = get_user_timezone(user)
    
    # Convert to user's timezone
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    dt_user = dt.astimezone(user_tz)
    return format_datetime(dt_user, locale=locale, format=format)

def format_number_localized(number, user=None):
    """Format number based on user's locale"""
    locale = get_locale()
    return format_number(number, locale=locale)

def get_localized_enum_value(enum_value, enum_type):
    """Get localized enum value"""
    if not enum_value:
        return ''
    
    # Create translation key
    key = f"{enum_type.__name__.lower()}.{enum_value.value}"
    return _(key)

# Template context processor
def inject_template_functions():
    """Inject utility functions into template context"""
    return {
        'format_currency_localized': format_currency_localized,
        'format_datetime_localized': format_datetime_localized,
        'format_number_localized': format_number_localized,
        'get_localized_enum_value': get_localized_enum_value,
        'available_languages': current_app.config['LANGUAGES']
    }
'''

print("Multilingual utility functions:")
print(i18n_utils)
