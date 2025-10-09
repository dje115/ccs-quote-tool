#!/usr/bin/env python3
"""
Translation management commands
"""

translation_commands = '''
# Translation Management Commands:

# 1. Extract translatable strings
pybabel extract -F babel.cfg -k _l -o messages.pot .

# 2. Initialize translation for a language (e.g., Spanish)
pybabel init -i messages.pot -d translations -l es

# 3. Update translations after adding new strings
pybabel update -i messages.pot -d translations

# 4. Compile translations
pybabel compile -d translations

# 5. Add new language (e.g., French)
pybabel init -i messages.pot -d translations -l fr

# Example workflow:
# 1. Make changes to templates/views
# 2. Run: pybabel extract -F babel.cfg -k _l -o messages.pot .
# 3. Run: pybabel update -i messages.pot -d translations
# 4. Edit translation files in translations/es/LC_MESSAGES/messages.po
# 5. Run: pybabel compile -d translations
# 6. Restart application
'''

print("Translation management commands:")
print(translation_commands)
