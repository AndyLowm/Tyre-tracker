from sqlmodel import SQLModel, Field, UniqueConstraint
from app.services.utils import normalised_string

# Import decimal and set up decimal constraint and positive constraints
# normalise strings in here for sqlmodels, username and acc_ame

class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    acc_name: str = Field(unique=True)

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True) 
    hash_pw: str
    acc_id: int = Field(foreign_key="account.id")

class AccountPrices(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "tyre_id", "acc_id",
            name= "unique_tyre_cost_price"
        ),
    )
    id: int | None = Field(default=None, primary_key=True)
    tyre_id: int = Field(foreign_key="tyre.id")
    acc_id: int = Field(foreign_key="account.id")
    cost_price: float = Field(ge=0)