from app.dependencies.templates import templates
from app.dependencies.database import Session_Dep
from app.dependencies.auth_flow import get_acc_id
from typing import Annotated
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import func, select
from app import models
from app.services import auth_service as AuthService
from app.routers.logins import log_failed_login, set_auth_cookie
from app.exceptions import InvalidCredentialsError

router = APIRouter(tags=["Webpages"])

@router.get('/login', response_class=HTMLResponse)
def view_login(request: Request):
    return templates.TemplateResponse(
        name="login.html.j2", request=request, context={"error": None}
    )

@router.post('/login', response_class=HTMLResponse)
def submit_login(
    request: Request,
    session: Session_Dep,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    ):
    try:
        acc_id = AuthService.verify_user(session, username, password)
    except InvalidCredentialsError as e:
        log_failed_login(request)
        return templates.TemplateResponse(
            name="login.html.j2",
            request=request,
            context={"error": str(e), "username": username},
            status_code=401,
        )
    response = RedirectResponse("/", status_code=303)
    set_auth_cookie(response, acc_id)
    return response

@router.get('/', response_class=HTMLResponse)
def view_homepage(
    request: Request,
    acc_id: Annotated[int, Depends(get_acc_id)],
    session: Session_Dep
    ):
    statement = select( func.sum(models.StockLocation.amount) ) 
    statement = statement.where(models.StockLocation.acc_id == acc_id)
    total_stock = session.exec(statement).first()
    return templates.TemplateResponse(
        name="home.html.j2", 
        request=request,
        context={
            "stats": {
                "total_stock": total_stock if total_stock is not None else 0
            }
        })