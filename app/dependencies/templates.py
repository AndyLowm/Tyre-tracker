from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Create relative path from current file
FILEROOT =  Path(__file__).resolve().parent.parent
TEMPLATES_DIR = FILEROOT / 'templates'

templates = Jinja2Templates(directory=TEMPLATES_DIR)

templates.env.globals["nav_items"] = [
    {"link_name": "Home", "path": "/"},
    {"link_name": "Stock Management", "path": "/stock-management/"},
    {"link_name": "Account", "path": "/account/"}
]