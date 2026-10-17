from pydantic import BaseModel, BeforeValidator, Field
from typing import Annotated
from sqlmodel import SQLModel

from app.services.utils import normalised_string, optional_normalised_string, normalise_string

class TyreBase(SQLModel):
    make: normalised_string
    model: normalised_string
    width: int = Field(index=True, gt=0)
    aspect_ratio: int = Field(gt=0)
    rim: int = Field(index=True)
    speed_rating: normalised_string

class TyreCostPublic(TyreBase):
    cost_price: float

class TyreCreate(TyreBase):
    cost_price: float = Field(gt=0)
    location_stock: dict[normalised_string, int] = Field(default_factory=dict)

class TyreCreateConfirm(TyreBase):
    tyre_id: int 
    cost_price: float
    stock_total: int

class TyreSearch(BaseModel):
    make: optional_normalised_string = None
    model: optional_normalised_string = None
    width: int | None = None
    aspect_ratio: int | None = None
    rim: int | None = None
    speed_rating: optional_normalised_string = None

class TyreStockAdjustment(BaseModel):
    location_amount: dict[normalised_string, int] = Field(default_factory=dict)

class TyreStockAdjustmentRequest(TyreStockAdjustment):
    cost_price: float = Field(gt=0)

class TyreStockPublicBase(BaseModel):
    stock_locations: dict[normalised_string, int]

class TyreStockPublic(TyreStockPublicBase):
    total_stock: int

class TyreInventoryPublic(TyreBase):
    cost_price: float = Field(gt=0)
    total_stock: int = Field(ge=0, default=0)

class StockMove(BaseModel):
    from_loc: normalised_string
    to_loc: normalised_string
    amount: int

