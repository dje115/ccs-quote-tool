import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app
from models import APISettings


with app.app_context():
    settings = APISettings.query.all()
    for setting in settings:
        print(setting.service_name, bool(setting.api_key), setting.api_key[:6] + '...' if setting.api_key else '')
