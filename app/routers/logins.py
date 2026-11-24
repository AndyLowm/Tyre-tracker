from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from app.dependencies.templates import templates
from typing import Annotated
from app.services.jwt_service import gen_token
from app.services import auth_service as AuthService
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies.database import Session_Dep
from app.schemas.auth import SignUp
from app.exceptions import InvalidCredentialsError, SignUpError
from app.dependencies.config import logger
from datetime import timedelta
import json
router = APIRouter(tags=["login"])

def log_failed_login(request: Request) -> None:
    client_data = {
        "client_ip": request.client.host if request.client else "UNKNOWN"
    }
    logger.warning(msg=json.dumps(client_data))

def set_auth_cookie(response: Response, acc_id: int) -> str:
    jwt_expire = timedelta(minutes=60)
    token = gen_token(payload={"sub": str(acc_id)}, exp_delta=jwt_expire)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=3600,
        samesite= "lax",
        httponly=True,
        secure=False #turn back to True for production
    )
    return token

# --------------------------------------------------------------
# TOKEN ROUTE --------------------------------------------------
# --------------------------------------------------------------

#Go build login and signup routes 
#Temp use get_acc_id with returning 1 to test then comment out in produciton
@router.post("/token")
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session_Dep,
    response: Response,
    request: Request
)->dict[str,str]:
    try:
        acc_id = AuthService.verify_user(session, form_data.username, form_data.password)
    except InvalidCredentialsError as e:
        log_failed_login(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
            )
    token = set_auth_cookie(response, acc_id)
    return {"access_token": token, "token_type": "bearer"}

# --------------------------------------------------------------
# SIGNUP ROUTE --------------------------------------------------
# --------------------------------------------------------------

def _signup_error(request: Request, message: str, username: str, code: int) -> HTMLResponse:
    return templates.TemplateResponse(
        name="signup.html.j2",
        request=request,
        context={"error": message, "username": username},
        status_code=code,
    )

@router.get('/signup', response_class=HTMLResponse, include_in_schema=False)
def view_signup(request: Request):
    return templates.TemplateResponse(
        name="signup.html.j2", request=request, context={"error": None}
    )

@router.post('/signup', response_class=HTMLResponse, include_in_schema=False)
def signup(
    request: Request,
    session: Session_Dep,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    confirm_password: Annotated[str, Form()],
):
    try:
        form_data = SignUp(username=username, password=password)
    except ValidationError:
        return _signup_error(
            request,
            "Username must be 4-24 characters and password 8-128 characters",
            username, status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    try:
        acc_id = AuthService.create_user_account(
            session, form_data.username, form_data.password, confirm_password
        )
    except SignUpError as e:
        return _signup_error(request, str(e), username, status.HTTP_400_BAD_REQUEST)
    session.commit()
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    set_auth_cookie(response, acc_id)
    return response
