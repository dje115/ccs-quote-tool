#!/usr/bin/env python3
"""
Template updates for multilingual support
"""

# Example template updates:

template_examples = '''
# templates/base.html - Add language selector
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
        <!-- Language Selector -->
        <div class="dropdown">
            <button class="btn btn-outline-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
                {{ get_locale().display_name }}
            </button>
            <ul class="dropdown-menu">
                {% for code, name in config.LANGUAGES.items() %}
                <li><a class="dropdown-item" href="{{ url_for('main.set_language', lang=code) }}">
                    {{ name }}
                </a></li>
                {% endfor %}
            </ul>
        </div>
    </div>
</nav>

# templates/lead_generation/dashboard.html - Multilingual text
<h1>{{ _('Lead Generation Dashboard') }}</h1>
<p>{{ _('Welcome to your lead generation dashboard. Here you can manage campaigns and view generated leads.') }}</p>

<button class="btn btn-primary">
    {{ _('Create New Campaign') }}
</button>

# templates/crm/customer_detail.html - Multilingual labels
<div class="card">
    <div class="card-header">
        <h5>{{ _('Customer Information') }}</h5>
    </div>
    <div class="card-body">
        <p><strong>{{ _('Company Name') }}:</strong> {{ customer.company_name }}</p>
        <p><strong>{{ _('Contact Email') }}:</strong> {{ customer.contact_email }}</p>
        <p><strong>{{ _('Business Sector') }}:</strong> {{ _(customer.business_sector.value) }}</p>
        <p><strong>{{ _('Status') }}:</strong> {{ _(customer.status.value) }}</p>
    </div>
</div>
'''

print("Template examples for multilingual support:")
print(template_examples)
