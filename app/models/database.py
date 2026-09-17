from sqlmodel import SQLModel, Field

class TyreBase(SQLModel):
    make: str
    model: str
    width: int = Field(index=True)
    aspect_ratio: int
    rim: int = Field(index=True)
    speed_rating: str

class Tyre(TyreBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cost_price: float = Field(gt=0)
    stock_total: int = Field(ge=0, default=0)

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