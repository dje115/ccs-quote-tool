#!/usr/bin/env python3
"""
Example translation files
"""

# translations/es/LC_MESSAGES/messages.po (Spanish):

spanish_translations = '''
# Spanish translations
msgid "Lead Generation Dashboard"
msgstr "Panel de Generación de Leads"

msgid "Welcome to your lead generation dashboard."
msgstr "Bienvenido a su panel de generación de leads."

msgid "Create New Campaign"
msgstr "Crear Nueva Campaña"

msgid "Customer Information"
msgstr "Información del Cliente"

msgid "Company Name"
msgstr "Nombre de la Empresa"

msgid "Contact Email"
msgstr "Correo de Contacto"

msgid "Business Sector"
msgstr "Sector Empresarial"

msgid "Status"
msgstr "Estado"

# Enum translations
msgid "business_sector.technology"
msgstr "Tecnología"

msgid "business_sector.healthcare"
msgstr "Salud"

msgid "business_sector.education"
msgstr "Educación"

msgid "lead_status.new"
msgstr "Nuevo"

msgid "lead_status.contacted"
msgstr "Contactado"

msgid "lead_status.qualified"
msgstr "Calificado"
'''

# translations/fr/LC_MESSAGES/messages.po (French):

french_translations = '''
# French translations
msgid "Lead Generation Dashboard"
msgstr "Tableau de Bord de Génération de Prospects"

msgid "Welcome to your lead generation dashboard."
msgstr "Bienvenue dans votre tableau de bord de génération de prospects."

msgid "Create New Campaign"
msgstr "Créer une Nouvelle Campagne"

msgid "Customer Information"
msgstr "Informations Client"

msgid "Company Name"
msgstr "Nom de l'Entreprise"

msgid "Contact Email"
msgstr "Email de Contact"

msgid "Business Sector"
msgstr "Secteur d'Activité"

msgid "Status"
msgstr "Statut"
'''

print("Example Spanish translations:")
print(spanish_translations[:500] + "...")
print("\nExample French translations:")
print(french_translations[:300] + "...")
