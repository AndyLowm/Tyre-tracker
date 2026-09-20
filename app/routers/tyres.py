from app.dependencies.config import settings, logger
from app.services.tyre_service import (
    tyre_duplicate_check, 
    create_tyre_inventory, 
    delete_tyre_record,
    check_archived_tyre_record,
    update_archived_inventory,
    calculate_new_stock_values
    )
from fastapi import APIRouter, HTTPException, status, Path
from sqlmodel import Field, select
from app.dependencies.database import Session_Dep
from typing import Annotated
from app.models.tyre import (
    Tyre, 
    TyreLocation, 
    TyreCreate, 
    TyreCreateConfirm,
    TyreStockAdjustmentRequest,
    TyreInventoryPublic
    )
router = APIRouter(tags=["Tyres"], prefix="/tyre")

@router.post(
        "/add-tyre",status_code=status.HTTP_201_CREATED,
          response_model= TyreCreateConfirm)
async def add_tyre(
    session: Session_Dep,
    payload: TyreCreate
)-> TyreCreateConfirm:
    
    if tyre_duplicate_check(session, payload):
        logger.warning(msg=f"Double entry of tyre {payload.make} {payload.model} attempted")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The tyre specification '{payload.make} {payload.model}' already exists.")
    archived_tyre = check_archived_tyre_record(session, payload)
    if archived_tyre:
         db_tyre, db_tyre_loc = update_archived_inventory(session, payload, archived_tyre)
    else:
        db_tyre, db_tyre_loc = create_tyre_inventory(session, payload)
    session.commit()
    session.refresh(db_tyre)
    session.refresh(db_tyre_loc)
    tyre_confirm_dict = db_tyre.model_dump(exclude={"id", "is_deleted"})
    tyre_loc_confirm_dict = db_tyre_loc.model_dump(exclude={"id"})
    combined_confim = tyre_confirm_dict | tyre_loc_confirm_dict
    return TyreCreateConfirm(**combined_confim)

@router.delete(
        "/remove-tyre/{tyre_id}",
        status_code=status.HTTP_200_OK)
async def delete_tyre(
    session: Session_Dep,
    tyre_id: Annotated[int, Path()]
)-> dict[str,str]:
    
    db_tyre = session.get(Tyre, tyre_id)

    if not db_tyre:
        logger.warning(msg=f"Tyre deletion from databse failed as tyre_id: {tyre_id} not found")
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Tyre id not found in database"
            )
    msg = delete_tyre_record(db_tyre, session)
    session.commit()
    return msg

@router.patch(
    "/add-stock/{tyre_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model= TyreInventoryPublic
    )
async def add_stock(
    session: Session_Dep,
    tyre_id: Annotated[int, Path()],
    payload: TyreStockAdjustmentRequest
)-> TyreInventoryPublic:
    db_tyre = session.get(Tyre,tyre_id)
    if not db_tyre:
        logger.warning(msg="Stock update failed as tyre_id not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tyre does not exist")
    
    db_tyre_loc = session.exec(select(TyreLocation).where(TyreLocation.tyre_id == tyre_id)).first()
    if not db_tyre_loc:
        logger.warning(msg=f"TyreLocation record missing for tyre_id: {tyre_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="record information missing for tyre id")

    updated_stock_loc, updated_stock = calculate_new_stock_values(db_tyre, db_tyre_loc,payload)

    db_tyre_loc.sqlmodel_update(updated_stock_loc)
    db_tyre.sqlmodel_update(updated_stock)
    session.add(db_tyre_loc)
    session.add(db_tyre)
    session.commit()

    session.refresh(db_tyre)
    session.refresh(db_tyre_loc)

    missing_keys = {
        "new_cost_price": db_tyre.cost_price,
        "new_stock_van": db_tyre_loc.stock_van,
        "new_stock_unit": db_tyre_loc.stock_unit,
        "new_total_stock": db_tyre.stock_total,
    }

    public_dict = (
        db_tyre.model_dump(
            exclude={"id", "cost_price", "stock_total", "is_deleted"}
        )
        | missing_keys
    )
    return TyreInventoryPublic(**public_dict)