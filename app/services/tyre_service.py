from sqlmodel import Session
from app.models.tyre import TyreCreate, Tyre, StockLocation, TyreStockAdjustmentRequest
from sqlmodel import select
from app.dependencies.config import logger

# =======================================================
# VALIDATION CHECKS
# =======================================================
def tyre_duplicate_check(session: Session, payload: TyreCreate)-> bool:
    """ Checks if tyres exists in database"""
    duplicate_check = session.exec(
    select(Tyre).where(
        Tyre.make == payload.make,
        Tyre.model == payload.model,
        Tyre.width == payload.width,
        Tyre.aspect_ratio == payload.aspect_ratio,
        Tyre.rim == payload.rim,
        Tyre.speed_rating == payload.speed_rating,
        Tyre.is_deleted == False
    )
    ).first()
    return bool(duplicate_check)

def check_archived_tyre_record(session: Session, payload: TyreCreate) -> None | Tyre:
    """ Checks DB for archived tyre and returns it """
    search_criteria = payload.model_dump(exclude={"cost_price", "location_stock"})
    search_criteria["is_deleted"] = True
    archived_tyre = session.exec(select(Tyre).filter_by(**search_criteria)).first()
    if not  archived_tyre:
        return None 
    return archived_tyre

# =======================================================
# INVENTORY CREATIONS / UPDATES
# =======================================================

def update_archived_inventory(session: Session, payload: TyreCreate, archived_tyre: Tyre) -> Tyre:
    """ updates archived tyre in database and returns updated archived records or None"""          
    new_stock_dict = payload.location_stock
    archived_tyre.is_deleted = False
    archived_tyre.cost_price = payload.cost_price

    for loc, amount in new_stock_dict.items():
        existing_loc = next((s for s in archived_tyre.stocks if s.location_name == loc),None)
        if existing_loc:
            existing_loc.amount = amount
        else:
            new_row = StockLocation(
                tyre_id = archived_tyre.id,
                location_name= loc,
                amount= amount
            )
            archived_tyre.stocks.append(new_row) 
    return archived_tyre

def create_tyre_inventory(payload: TyreCreate)->Tyre:
    """ adds tyre and stock info to both tables in databse """
    stocks = [StockLocation(location_name= loc, amount= amount) for loc, amount in payload.location_stock.items()]
    new_tyre_dict = payload.model_dump(exclude={"location_stock"})
    new_tyre_dict['stocks'] = stocks
    new_tyre = Tyre(**new_tyre_dict)
    return new_tyre

def calculate_new_stock_values(
        db_tyre: Tyre, 
        payload: TyreStockAdjustmentRequest
        )-> None:
    """ Calculate new stock amounts and new cost price """
    new_stock_value = sum(payload.location_amount.values())*payload.cost_price
    total_stock = db_tyre.stock_total + sum(payload.location_amount.values())
    old_stock_value = db_tyre.cost_price * db_tyre.stock_total
    if total_stock > 0:
        new_cost_price = round(( (new_stock_value + old_stock_value)/ total_stock ),2)
    else:
        new_cost_price = db_tyre.cost_price
    db_tyre.cost_price = new_cost_price

    for loc, amount in payload.location_amount.items():
        location = next((l for l in db_tyre.stocks if l.location_name == loc), None )
        if location:
            location.amount += amount
        else:
            new_loc = StockLocation(
                location_name=loc,
                amount= amount
            )
            db_tyre.stocks.append(new_loc)
    return

# =======================================================
# INVENTORY DELETIONS
# =======================================================

def delete_tyre_record(db_tyre: Tyre, session: Session)-> dict[str,str]:
    """ Soft Tyre delete from database """

    msg = f"{db_tyre.make} {db_tyre.model} - {db_tyre.width}/{db_tyre.aspect_ratio}R{db_tyre.rim} deleted"
    db_tyre.is_deleted = True
    session.add(db_tyre)
    return {"status": "Succesfully deleted","msg": msg}