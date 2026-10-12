from app.schemas import TyreBase
from typing import Annotated
from sqlmodel import Relationship, SQLModel, Field

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