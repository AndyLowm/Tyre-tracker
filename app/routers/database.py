from app.dependencies.config import settings
from app.services.tyre_service import tyre_duplicate_check, create_tyre_inventory
from fastapi import APIRouter, HTTPException
from sqlmodel import Field, select
from app.dependencies.database import Session_Dep
from typing import Annotated
from app.models.database import Tyre, TyreLocation, TyreCreate, TyreCreateConfirm
router = APIRouter(tags=["Database"], prefix="/tyre")

@router.post("/add-tyre",status_code=201, response_model= TyreCreateConfirm)
async def add_tyre(
    session: Session_Dep,
    payload: TyreCreate
)-> TyreCreateConfirm:
    
    if tyre_duplicate_check(session, payload):
        raise HTTPException(status_code=400,
                            detail=f"The tyre specification '{payload.make} {payload.model}' already exists.")
    
    db_tyre, db_tyre_loc = create_tyre_inventory(session, payload)
    session.commit()
    session.refresh(db_tyre)
    session.refresh(db_tyre_loc)
    tyre_confirm_dict = db_tyre.model_dump(exclude={"id"})
    tyre_loc_confirm_dict = db_tyre_loc.model_dump(exclude={"id"})
    combined_confim = tyre_confirm_dict | tyre_loc_confirm_dict
    return TyreCreateConfirm(**combined_confim)

