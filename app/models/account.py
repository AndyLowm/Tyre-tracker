from sqlmodel import SQLModel, Field
from app.services.utils import normalised_string

class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    acc_name: str

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True) 
    hash_pw: str
    acc_id: int = Field(foreign_key="account.id")

class AccountPrices(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tyre_id: int = Field(foreign_key="tyre.id")
    acc_id: int = Field(foreign_key="account.id")
    cost_price: float = Field(ge=0)