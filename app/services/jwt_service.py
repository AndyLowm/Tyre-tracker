import jwt
from app.dependencies.config import settings as env
from datetime import datetime, timezone, timedelta

def gen_token(payload: dict, exp_delta: timedelta = None)-> str:
    if exp_delta:
        exp_time = datetime.now(timezone.utc) + exp_delta
    else:
        exp_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    data = payload.copy()
    data.update({"exp" : exp_time})
    token = jwt.encode(payload=data, key=env.jwt_key, algorithm=env.jwt_algo)
    return token
