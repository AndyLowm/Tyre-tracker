from app.dependencies.database import Session_Dep
from app.models import Account, User
from pwdlib import PasswordHash
from sqlmodel import select
from app.services.utils import normalise_string

def create_user_account(
        session: Session_Dep,
        username: str,
        password: str
)-> None:
    normalised_username = normalise_string(username)
    new_account = Account(
        acc_name= normalised_username
    )

    session.add(new_account)
    session.flush()
    
    hasher = PasswordHash.recommended()
    hashed_pw = hasher.hash(password=password)
    new_user = User(
        username=normalised_username,
        hash_pw=hashed_pw,
        acc_id=new_account.id
    )
    session.add(new_user)

def verify_user(
        session: Session_Dep,
        username: str,
        password: str
)->tuple[bool, int | None]:
    """ Verfies username and password, runs dummy hash to prevent timing attack """
    normalised_username = normalise_string(username)
    hasher = PasswordHash.recommended()
    if len(normalised_username) > 128:
        return False, None
    
    verified_user = session.exec(select(User).where(User.username == normalised_username)).first()
    
    if not verified_user:
        dummy_hash = hasher.hash(password)
        hasher.verify(password="DUMMY", hash=dummy_hash)
        return False, None
    pw_verified = hasher.verify(password=password, hash=verified_user.hash_pw)
    if not pw_verified:
        return False, None
    return True, verified_user.acc_id