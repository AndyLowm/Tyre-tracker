from app.dependencies.templates import templates
from app.dependencies.database import Session_Dep
from app.dependencies.auth_flow import get_acc_id
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import func, select
from app import models

router = APIRouter(tags=["Webpages"])

@router.get('/', response_class=HTMLResponse)
def view_homepage(
    request: Request,
    acc_id: Annotated[int, Depends(get_acc_id)],
    session: Session_Dep
    ):
    statement = select( func.sum(models.StockLocation.amount) ) 
    statement = statement.where(models.StockLocation == acc_id)
    total_stock = session.exec(statement).first()
    return templates.TemplateResponse(
        name="home.html.j2", 
        request=request,
        context={
            "stats": {
                "total_stock": total_stock if total_stock is not None else 0
            }
        })