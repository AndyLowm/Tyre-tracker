from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from typing import Annotated
from app.dependencies.auth_flow import get_acc_id
from app.services.jwt_service import gen_token
from app.services.auth_service import create_user_account, verify_user
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies.database import Session_Dep
from app.models import User, Account
from app.models.auth import SignUp
from sqlmodel import select
from app.dependencies.config import logger
from datetime import timedelta
router = APIRouter(tags=["login"])

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
    username, password = form_data.username, form_data.password
    verified, acc_id = verify_user(session, username, password)
    if not verified:
        client_ip = request.client.host if request.client else "UNKNOWN"
        logger.warning(
            msg=f"failed log in attempt CLIENT_IP: {client_ip}, attempted USERNAME: {username}"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
            )
    jwt_expire = timedelta(minutes=60)
    token = gen_token(payload={"sub": str(acc_id)}, exp_delta=jwt_expire)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=3600,
        samesite= "lax",
        secure=False #turn back to True for production
    )
    return {"access_token": token, "token_type": "bearer"}

# --------------------------------------------------------------
# SIGNUP ROUTE --------------------------------------------------
# --------------------------------------------------------------

@router.post('/signup')
async def signup(
    session: Session_Dep,
    form_data: SignUp
)-> dict[str,str]:
    username, password = form_data.username, form_data.password
    user_exists = session.exec(select(User).where(User.username == username)).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sign up failed"
            )
    create_user_account(session, username, password)
    session.commit()
    return {"msg": "Sign up succesfull"}
