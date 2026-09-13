from pathlib import Path
from fastapi.templating import Jinja2Templates

# Create relative path from current file
FILEROOT =  Path(__file__).resolve().parent.parent
TEMPLATES_DIR = FILEROOT / 'templates'

templates = Jinja2Templates(directory=TEMPLATES_DIR)