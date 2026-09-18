from app.dependencies.config import settings
from app.services.tyre_service import (
    tyre_duplicate_check, 
    create_tyre_inventory, 
    delete_tyre_record,
    check_archived_tyre_record,
    update_archived_inventory
    )
from fastapi import APIRouter, HTTPException, status, Path
from sqlmodel import Field, select
from app.dependencies.database import Session_Dep
from typing import Annotated
from app.models.tyre import Tyre, TyreLocation, TyreCreate, TyreCreateConfirm
router = APIRouter(tags=["Tyres"], prefix="/tyre")

@router.post(
        "/add-tyre",status_code=status.HTTP_201_CREATED,
          response_model= TyreCreateConfirm)
async def add_tyre(
    session: Session_Dep,
    payload: TyreCreate
)-> TyreCreateConfirm:
    
    if tyre_duplicate_check(session, payload):
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
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Tyre id not found in database"
            )
    msg = delete_tyre_record(db_tyre, session)
    session.commit()
    return msg