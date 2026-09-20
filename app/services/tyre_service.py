from sqlmodel import Session
from app.models.tyre import TyreCreate, Tyre, TyreLocation, TyreStockAdjustmentRequest
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
    search_criteria = payload.model_dump(exclude={"id", "cost_price", "stock_van", "stock_unit"})
    search_criteria["is_deleted"] = True
    archived_tyre = session.exec(select(Tyre).filter_by(**search_criteria)).first()
    if not  archived_tyre:
        return None 
    return archived_tyre

# =======================================================
# INVENTORY CREATIONS / UPDATES
# =======================================================

def create_db_tyre(payload: TyreCreate)-> Tyre:
    """ Creates and returns Tyre model instance """
    total_stock = payload.stock_unit + payload.stock_van    
    tyre_dict = payload.model_dump(exclude={"stock_van", "stock_unit"})
    tyre_dict["stock_total"] = total_stock
    return Tyre(**tyre_dict)

def update_archived_inventory(session: Session, payload: TyreCreate, archived_tyre: Tyre) -> tuple[Tyre, TyreLocation]:
    """ updates archived tyre in database and returns updated archived records or None"""          
    total_stock = payload.stock_unit + payload.stock_van
    archived_tyre.stock_total = total_stock
    archived_tyre.cost_price = payload.cost_price
    archived_tyre.is_deleted = False
    session.add(archived_tyre)

    archived_tyre_loc = session.exec(select(TyreLocation).where(TyreLocation.tyre_id == archived_tyre.id)).first()
    if not archived_tyre_loc:
        archived_tyre_loc = TyreLocation(
            tyre_id= archived_tyre.id,
            in_van= payload.stock_van > 0,
            in_unit= payload.stock_unit > 0,
            stock_unit= payload.stock_unit,
            stock_van= payload.stock_van
        )
    archived_tyre_loc.stock_van = payload.stock_van
    archived_tyre_loc.stock_unit = payload.stock_unit
    archived_tyre_loc.in_unit = payload.stock_unit > 0
    archived_tyre_loc.in_van = payload.stock_van > 0
    session.add(archived_tyre_loc)

    return (archived_tyre, archived_tyre_loc)

def create_tyre_inventory(session: Session, payload: TyreCreate)->tuple[Tyre,TyreLocation]:
    """ adds tyre and stock info to both tables in databse """
    db_tyre = create_db_tyre(payload)
    session.add(db_tyre)
    session.flush()

    db_tyre_loc = TyreLocation(
        tyre_id= db_tyre.id,
        stock_unit= payload.stock_unit,
        stock_van= payload.stock_van,
        in_van= payload.stock_van > 0,
        in_unit= payload.stock_unit > 0
    )

    session.add(db_tyre_loc)
    session.flush()
    return (db_tyre, db_tyre_loc)

def calculate_new_stock_values(
        db_tyre: Tyre, 
        db_tyre_loc: TyreLocation, 
        payload: TyreStockAdjustmentRequest
        )-> tuple[dict,dict]:
    """ Calculate new stock amounts and new cost price """
    new_unit_stock = payload.stock_unit + db_tyre_loc.stock_unit
    new_van_stock =  payload.stock_van + db_tyre_loc.stock_van

    combine_stock_total = payload.stock_van + payload.stock_unit + db_tyre.stock_total

    old_stock_value = db_tyre.cost_price * db_tyre.stock_total
    new_stock_value = (payload.stock_unit + payload.stock_van) * payload.cost_price
    if combine_stock_total > 0:
        new_cost_price = round((old_stock_value + new_stock_value) / combine_stock_total,2)
    else:
        new_cost_price = db_tyre.cost_price
    
    updated_stock_loc = {
        "stock_unit": new_unit_stock,
        "stock_van": new_van_stock,
        "in_unit": new_unit_stock > 0,
        "in_van": new_van_stock > 0
        }
    updated_stock = {
        "cost_price": new_cost_price,
        "stock_total": new_unit_stock + new_van_stock
    }
    return (updated_stock_loc, updated_stock)

# =======================================================
# INVENTORY DELETIONS
# =======================================================

def delete_tyre_record(db_tyre: Tyre, session: Session)-> dict[str,str]:
    """ Soft Tyre delete from database """

    msg = f"{db_tyre.make} {db_tyre.model} - {db_tyre.width}/{db_tyre.aspect_ratio}R{db_tyre.rim} deleted"
    db_tyre.is_deleted = True
    session.add(db_tyre)
    return {"status": "Succesfully deleted","msg": msg}