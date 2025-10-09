#!/usr/bin/env python3
"""
Routes for language switching
"""

# Add to main routes or create new language_routes.py:

language_routes = '''
# routes/language.py
from flask import Blueprint, redirect, url_for, request, session, flash
from flask_babel import refresh

language_bp = Blueprint('language', __name__)

@language_bp.route('/set_language/<lang>')
def set_language(lang):
    """Set user's preferred language"""
    if lang in current_app.config['LANGUAGES']:
        session['language'] = lang
        
        # Update user preference if logged in
        if current_user.is_authenticated:
            current_user.language = lang
            db.session.commit()
        
        flash(_('Language changed to %(language)s', language=current_app.config['LANGUAGES'][lang]))
        refresh()  # Refresh translations
    
    # Redirect back to the page they came from
    return redirect(request.referrer or url_for('main.dashboard'))

@language_bp.route('/language/<lang>')
def change_language(lang):
    """Alternative language switching route"""
    return set_language(lang)
'''

print("Language switching routes:")
print(language_routes)
