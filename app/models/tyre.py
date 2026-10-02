from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from typing import Annotated
# refactor routes and sessions taking in to account the 2 new tables of Account and AccountPrices
#Also note that cost_price has been removed from the Tyre class
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

class TyreBase(SQLModel):
    make: str
    model: str
    width: int = Field(index=True, gt=0 )
    aspect_ratio: int = Field(gt=0)
    rim: int = Field(index=True)
    speed_rating: str

class Tyre(TyreBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    stocks: list["StockLocation"] = Relationship(back_populates="tyre")
    def get_stock_total(self, acc_id: int) -> int:
        return sum(item.amount for item in self.stocks if item.acc_id == acc_id)

class StockLocation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tyre_id : int = Field(foreign_key="tyre.id")
    acc_id: int = Field(foreign_key="account.id")
    location_name: str
    amount: int = Field(default=0, ge=0)
    tyre: Tyre = Relationship(back_populates="stocks")

class TyreCreate(TyreBase):
    cost_price: float = Field(gt=0)
    location_stock: dict[str,int] = Field(default_factory=dict)

class TyreCreateConfirm(TyreBase):
    tyre_id: int 
    cost_price: float
    stock_total: int

class TyreStockAdjustmentRequest(BaseModel):
    location_amount : dict[str,Annotated[int, Field(gt=0)]]
    cost_price: float = Field(gt=0)

class TyreInventoryPublic(TyreBase):
    cost_price: float = Field(gt=0)
    total_stock: int = Field(ge=0, default=0)
