from app.dependencies.database import Session_Dep
from app.models import Account, User
from pwdlib import PasswordHash
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.services.utils import normalise_string
from app.exceptions import InvalidCredentialsError, SignUpError

hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash("not-a-real-password")

def username_taken(session: Session_Dep, username: str) -> bool:
    return session.exec(select(User).where(User.username == username)).first() is not None

def create_user_account(
        session: Session_Dep,
        username: str,
        password: str,
        confirm_password: str
)-> int:
    """
    Create an account and its user, returning the new account id.
    Raises SignUpError if the passwords differ or the username is taken.
    """
    if password != confirm_password:
        raise SignUpError("Passwords do not match")
    normalised_username = normalise_string(username)
    if username_taken(session, normalised_username):
        raise SignUpError("Sign up failed, try a different username")
    hashed_pw = hasher.hash(password=password)

    new_account = Account(
        acc_name= normalised_username
    )
    # acc_name and username are both unique and both hold the username, so if two
    # sign-ups pass the check above at the same time the DB rejects the second here
    try:
        session.add(new_account)
        session.flush()

        new_user = User(
            username=normalised_username,
            hash_pw=hashed_pw,
            acc_id=new_account.id
        )
        session.add(new_user)
        session.flush()
    except IntegrityError as e:
        if any(col in str(e.orig) for col in ("username", "acc_name")):
            raise SignUpError("Sign up failed, try a different username") from e
        raise
    return new_account.id


def verify_user(
        session: Session_Dep,
        username: str,
        password: str
)-> int:
    """
    Return the account id if the credentials are valid, otherwise raise InvalidCredentialsError.
    Always runs one hash verification so timing doesn't reveal whether a username exists.
    """
    normalised_username = normalise_string(username)
    user = None
    if len(normalised_username) <= 128:
        user = session.exec(select(User).where(User.username == normalised_username)).first()
    stored_hash = user.hash_pw if user else DUMMY_HASH
    password_ok = hasher.verify(password=password, hash=stored_hash)

    if user is None or not password_ok:
        raise InvalidCredentialsError("Invalid username or password")
    return user.acc_id