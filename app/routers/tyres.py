from app.dependencies.config import settings, logger
from app.services.tyre_service import TyreService
from fastapi import APIRouter, HTTPException, status, Path, Depends
from sqlmodel import Field, select
from app.dependencies.database import Session_Dep
from app.dependencies.auth_flow import get_acc_id
from typing import Annotated
from app.models.tyre import (
    Tyre, 
    StockLocation, 
    TyreCreate, 
    TyreCreateConfirm,
    TyreStockAdjustmentRequest,
    TyreInventoryPublic,
    AccountPrices
    )
router = APIRouter(tags=["Tyres"], prefix="/tyre")
#refactor this!
@router.post(
        "/add-tyre",status_code=status.HTTP_201_CREATED,
          response_model= TyreCreateConfirm)
async def add_tyre(
    session: Session_Dep,
    acc_id: Annotated[int, Depends(get_acc_id)],
    payload: TyreCreate 
)-> TyreCreateConfirm:
    TyreConfirmation = TyreService.add_tyre_master(session, payload, acc_id)
    session.commit()
    return TyreConfirmation


@router.patch(
    "/add-stock/{tyre_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model= TyreInventoryPublic
    )
async def add_stock(
    session: Session_Dep,
    tyre_id: Annotated[int, Path()],
    acc_id: Annotated[int, Depends(get_acc_id)],
    payload: TyreStockAdjustmentRequest
)-> TyreInventoryPublic:
    
    tyre_data = session.get(Tyre,tyre_id)
    if not tyre_data:
        logger.warning(msg="Stock update failed as tyre_id not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tyre does not exist")

    old_stock_total = tyre_data.get_stock_total(acc_id)

    TyreService.create_and_update_stock_location_rows(
        session, tyre_data, acc_id, payload.location_amount
    )
    AccountP = TyreService.create_or_update_account_price(session,acc_id,tyre_id,payload.cost_price,payload.location_amount,old_stock_total)
    public_tyre_dict = tyre_data.model_dump(exclude={"id", "stocks"}) | {"cost_price": AccountP.cost_price}
    public_tyre_dict["total_stock"] = tyre_data.get_stock_total(acc_id) 
    session.commit()
    return TyreInventoryPublic(**public_tyre_dict)