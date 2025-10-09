#!/usr/bin/env python3
"""
Multilingual application configuration example
"""

# Add to app.py:

multilingual_config = '''
# app.py - Multilingual Configuration

from flask_babel import Babel, get_locale
from flask import request, session

def create_app():
    app = Flask(__name__)
    
    # Babel configuration
    app.config['LANGUAGES'] = {
        'en': 'English',
        'es': 'Español', 
        'fr': 'Français',
        'de': 'Deutsch',
        'it': 'Italiano',
        'pt': 'Português',
        'nl': 'Nederlands',
        'pl': 'Polski',
        'zh': '中文',
        'ja': '日本語',
        'ar': 'العربية'
    }
    
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
    
    # Initialize Babel
    babel = Babel(app)
    
    @babel.localeselector
    def get_locale():
        # 1. Check URL parameter
        if request.args.get('lang'):
            session['language'] = request.args.get('lang')
            return request.args.get('lang')
        
        # 2. Check session
        if session.get('language'):
            return session['language']
        
        # 3. Check user preference from database
        if current_user.is_authenticated and current_user.language:
            return current_user.language
        
        # 4. Check browser language
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'
    
    return app
'''

print("Multilingual configuration for app.py:")
print(multilingual_config)
