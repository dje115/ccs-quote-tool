# Multilingual Implementation Steps

## Phase 1: Setup and Configuration
1. **Install dependencies**
   ```bash
   pip install Flask-Babel==4.0.0 Babel==2.12.1
   ```

2. **Update requirements.txt**
   ```
   Flask-Babel==4.0.0
   Babel==2.12.1
   ```

3. **Configure app.py**
   - Add Babel configuration
   - Set up language selector
   - Configure supported languages

4. **Create babel.cfg**
   - Configure extraction settings

## Phase 2: Database Updates
1. **Add language fields to User model**
   ```python
   language = Column(String(10), default='en')
   timezone = Column(String(50), default='UTC')
   ```

2. **Add language fields to Customer model**
   ```python
   language = Column(String(10), default='en')
   currency = Column(String(3), default='GBP')
   ```

3. **Run database migration**
   ```python
   # Create migration script
   # Add new columns to existing tables
   ```

## Phase 3: Template Updates
1. **Update all templates**
   - Wrap text in `{{ _('text') }}`
   - Add language selector to base template
   - Update forms and labels

2. **Create translation files**
   - Extract strings: `pybabel extract -F babel.cfg -k _l -o messages.pot .`
   - Initialize languages: `pybabel init -i messages.pot -d translations -l es`

## Phase 4: Routes and Utilities
1. **Add language switching routes**
2. **Create utility functions**
3. **Add template context processors**

## Phase 5: Translation and Testing
1. **Translate strings**
   - Edit .po files for each language
   - Compile translations: `pybabel compile -d translations`

2. **Test all functionality**
   - Language switching
   - Form submissions
   - Data display
   - Currency formatting
   - Date/time formatting

## Phase 6: Advanced Features
1. **AI prompt translations**
   - Translate system prompts for different languages
   - Handle AI responses in multiple languages

2. **Email templates**
   - Multilingual email templates
   - Localized email content

3. **PDF generation**
   - Multilingual PDF templates
   - Localized document generation

## Priority Languages
1. **English (en)** - Default
2. **Spanish (es)** - High priority
3. **French (fr)** - Medium priority
4. **German (de)** - Medium priority
5. **Portuguese (pt)** - Low priority
6. **Italian (it)** - Low priority
7. **Dutch (nl)** - Low priority

## Estimated Timeline
- **Phase 1-2**: 2-3 days
- **Phase 3**: 3-4 days
- **Phase 4**: 1-2 days
- **Phase 5**: 2-3 days
- **Phase 6**: 3-5 days

**Total**: 11-17 days for full implementation
