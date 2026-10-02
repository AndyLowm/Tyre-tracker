from fastapi.security import APIKeyCookie
from fastapi import Depends, HTTPException, status, Request
from sqlmodel import select
from app.dependencies.database import Session_Dep
from typing import Annotated
import jwt
from app.models import Account, User
from app.dependencies.config import settings as env
from pwdlib import PasswordHash
from app.dependencies.config import logger


async def get_acc_id(
        session: Session_Dep,
        request: Request,
)-> int:
    """ Decrypts jwt token, checks user is valid and returns id """
    token = request.cookies.get("access_token")
    if not token:
        attempted_path = request.url.path
        http_method = request.method
        client_ip = request.client.host if request.client else "UNKNOWN"
        logger.warning(msg=f"route: {attempted_path} with HTTP Method {http_method} denied client IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        verified_acc_id = jwt.decode(jwt=token, key=env.jwt_key, algorithms=[env.jwt_algo])["sub"]
    except Exception as e:
        print(f"🔴 Error: {str(e)}")
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Unauthorized access",
            headers={"WWW-Authenticate": "Bearer"}
        )
    acc_id = int(verified_acc_id)
    account = session.get(Account, acc_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return acc_id

