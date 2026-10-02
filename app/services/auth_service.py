from app.dependencies.database import Session_Dep
from app.models import Account, User
from pwdlib import PasswordHash
from sqlmodel import select

def create_user_account(
        session: Session_Dep,
        username: str,
        password: str
)-> None:
    new_account = Account(
        acc_name=username
    )

    session.add(new_account)
    session.flush()
    
    hasher = PasswordHash.recommended()
    hashed_pw = hasher.hash(password=password)
    new_user = User(
        username=username,
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
    hasher = PasswordHash.recommended()
    verified_user = session.exec(select(User).where(User.username == username)).first()
    if not verified_user:
        dummy_hash = hasher.hash("DUMMY")
        hasher.verify(password="DUMMY", hash=dummy_hash)
        return False, None
    pw_verified = hasher.verify(password=password, hash=verified_user.hash_pw)
    if not pw_verified:
        return False, None
    return True, verified_user.acc_id