import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app
from models import AIPrompt

with app.app_context():
    prompts = AIPrompt.query.all()
    if not prompts:
        print('No prompts found')
    for prompt in prompts:
        print(prompt.id, prompt.prompt_type, prompt.name, prompt.is_default, prompt.is_active)


