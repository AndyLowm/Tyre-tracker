from app.dependencies.config import settings, logger
from app.services import tyre_service as TyreService
from fastapi import APIRouter, HTTPException, status, Path, Depends, Query
from sqlmodel import Field, select
from sqlalchemy.orm import contains_eager
from app.dependencies.database import Session_Dep
from app.dependencies.auth_flow import get_acc_id
from typing import Annotated
from app import schemas
from app import models
router = APIRouter(tags=["Tyres"], prefix="/tyre")
#refactor this!
@router.post(
        "/add-tyre",status_code=status.HTTP_201_CREATED,
          response_model= schemas.TyreCreateConfirm)
async def add_tyre(
    session: Session_Dep,
    acc_id: Annotated[int, Depends(get_acc_id)],
    payload: schemas.TyreCreate 
)-> schemas.TyreCreateConfirm:
    TyreConfirmation = TyreService.add_tyre_master(session, payload, acc_id)
    session.commit()
    return TyreConfirmation


@router.patch(
    "/add-stock/{tyre_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model= schemas.TyreInventoryPublic
    )
async def add_stock(
    session: Session_Dep,
    tyre_id: Annotated[int, Path()],
    acc_id: Annotated[int, Depends(get_acc_id)],
    payload: schemas.TyreStockAdjustmentRequest
)-> schemas.TyreInventoryPublic:
    
    tyre_data = session.get(models.Tyre,tyre_id)
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
'/remove-stock/{tyre_id}', 
status_code= status.HTTP_200_OK,
response_model= schemas.TyreStockPublic
)
async def remove_stock(
    session: Session_Dep,
    tyre_id: Annotated[int, Path()],
    acc_id: Annotated[int, Depends(get_acc_id)],
    payload: schemas.TyreStockAdjustment
)-> schemas.TyreStockPublic:
    tyre_data = session.get(models.Tyre,tyre_id)
    if not tyre_data:
        logger.info(msg="Stock update failed as tyre_id not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tyre does not exist")
    try:
        updated_tyre_public = TyreService.remove_stock_master(session, payload, acc_id, tyre_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= str(e))
    session.commit()
    return updated_tyre_public

@router.get(
    '/search-tyres',
    status_code= status.HTTP_200_OK,
    response_model= list[schemas.TyreCostPublic]
    )
async def search_for_tyre(
        session: Session_Dep,
        acc_id: Annotated[int, Depends(get_acc_id)],
        filters: Annotated[schemas.TyreSearch, Depends()]
)-> list[schemas.TyreCostPublic]:
    try:
        tyre_list= TyreService.tyre_search(filters, session, acc_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= str(e))
    except LookupError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= str(e))
    return tyre_list
# Routes
# move stock    
# display individual tyre stocks
# display all tyres with stock amounts total