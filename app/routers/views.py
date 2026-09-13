from app.dependencies.templates import templates
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Webpages"])

@router.get('/', response_class=HTMLResponse)
def view_homepage(request: Request):
    return templates.TemplateResponse(name="base.html", request=request)