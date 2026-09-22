from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from typing import Annotated

class TyreBase(SQLModel):
    make: str
    model: str
    width: int = Field(index=True, gt=0 )
    aspect_ratio: int = Field(gt=0)
    rim: int = Field(index=True)
    speed_rating: str

class Tyre(TyreBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cost_price: float = Field(gt=0)
    is_deleted : bool = Field(default=False)
    stocks: list["StockLocation"] = Relationship(back_populates="tyre")

    @property
    def stock_total(self):
        return sum(item.amount for item in self.stocks)

class StockLocation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tyre_id : int = Field(foreign_key="tyre.id")
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
