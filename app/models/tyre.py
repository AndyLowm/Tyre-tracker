from sqlmodel import SQLModel, Field
from pydantic import BaseModel

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
    stock_total: int = Field(ge=0, default=0)
    is_deleted : bool = Field(default=False)

class TyreLocation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tyre_id: int = Field(foreign_key="tyre.id")
    in_van : bool = Field(default=False)
    in_unit: bool = Field(default=False)
    stock_van: int = Field(ge=0, default=0)
    stock_unit: int = Field(ge=0, default=0)

class TyreCreate(TyreBase):
    cost_price: float = Field(gt=0)
    stock_van: int = Field(ge=0, default=0)
    stock_unit: int = Field(ge=0, default=0)

class TyreCreateConfirm(TyreBase):
    tyre_id: int = Field(foreign_key="tyre.id")
    in_van : bool
    in_unit: bool
    stock_van: int
    stock_unit: int
    cost_price: float
    stock_total: int

class TyreStockAdjustmentRequest(BaseModel):
    stock_van: int = Field(ge=0, default=0)
    stock_unit: int = Field(ge=0, default=0)
    cost_price: float = Field(gt=0)

class TyreInventoryPublic(TyreBase):
    new_cost_price: float = Field(gt=0)
    new_stock_van: int = Field(ge=0, default=0)
    new_stock_unit: int = Field(ge=0, default=0)
    new_total_stock: int = Field(ge=0, default=0)
