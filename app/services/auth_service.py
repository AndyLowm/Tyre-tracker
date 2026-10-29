from app.dependencies.database import Session_Dep
from app.models import Account, User
from pwdlib import PasswordHash
from sqlmodel import select
from app.services.utils import normalise_string

hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash("not-a-real-password")

def create_user_account(
        session: Session_Dep,
        username: str,
        password: str
)-> None:
    normalised_username = normalise_string(username)
    hashed_pw = hasher.hash(password=password)

    new_account = Account(
        acc_name= normalised_username
    )

    session.add(new_account)
    session.flush()
    
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
)-> int | None:
    """
    Return the account id if the credentials are valid, otherwise None. 
    Always runs one hash verification so timing doesn't reveal whether a username exists.
    """
    normalised_username = normalise_string(username)
    user = None
    if len(normalised_username) <= 128:
        user = session.exec(select(User).where(User.username == normalised_username)).first()
    stored_hash = user.hash_pw if user else DUMMY_HASH
    password_ok = hasher.verify(password=password, hash=stored_hash)

    if user is None or not password_ok:
        return None
    return user.acc_id