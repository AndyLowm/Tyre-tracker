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
from user_agents import parse
import json


async def get_acc_id(
        session: Session_Dep,
        request: Request,
)-> int:
    """ Decrypts jwt token, checks user is valid and returns id """
    token = request.cookies.get("access_token")
    if not token:
        raw_agent = request.headers.get("user-agent", "UNKNOWN")
        meta_data = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "UNKNOWN"
        }
        if raw_agent != "UNKNOWN":
            ua = parse(raw_agent)
            device_sum = {
                "device": f"{ua.device.brand}-{ua.device.model}-{ua.device.family}" if ua.is_mobile else "Desktop",
                "broswer": ua.get_os(),
            }
            meta_data["device_summary"] = device_sum

        meta_json = json.dumps(meta_data)
        logger.warning(msg= meta_json)
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

