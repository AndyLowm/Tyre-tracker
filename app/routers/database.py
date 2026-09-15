from app.dependencies.config import settings
from fastapi import APIRouter
from sqlmodel import Field, select
from app.dependencies.database import Session_Dep
from typing import Annotated

router = APIRouter(tags=["Database"], prefix="/database")

@router.post("/add-tyre")
async def add_tyre(
    session: Session_Dep
):
    return
