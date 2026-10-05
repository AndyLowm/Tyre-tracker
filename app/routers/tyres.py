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
    TyreStockAdjustment,
    TyreInventoryPublic,
    AccountPrices,
    TyreStockPublic
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
        logger.info(msg="Stock update failed as tyre_id not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tyre does not exist")

    public_tyre_payload = TyreService.add_tyre_stock_master(
        session,
        acc_id,
        tyre_data,
        payload
    )
    session.commit()
    return public_tyre_payload

@router.post('' \
'remove-stock/{tyre_id}', 
status_code= status.HTTP_200_OK,
response_model= TyreStockPublic
)
async def remove_stock(
    session: Session_Dep,
    tyre_id: Annotated[int, Path()],
    acc_id: Annotated[int, Depends(get_acc_id)],
    payload: TyreStockAdjustment
)-> TyreStockPublic:
    tyre_data = session.get(Tyre,tyre_id)
    if not tyre_data:
        logger.info(msg="Stock update failed as tyre_id not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tyre does not exist")
    try:
        updated_tyre_public = TyreService.remove_stock_master(session, payload, acc_id, tyre_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= str(e))
    session.commit()
    return updated_tyre_public