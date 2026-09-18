from sqlmodel import Session
from app.models.tyre import TyreCreate, Tyre, TyreLocation
from sqlmodel import select

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

# =======================================================
# INVENTORY DELETIONS
# =======================================================

def delete_tyre_record(db_tyre: Tyre, session: Session)-> dict[str,str]:
    """ Soft Tyre delete from database """

    msg = f"{db_tyre.make} {db_tyre.model} - {db_tyre.width}/{db_tyre.aspect_ratio}R{db_tyre.rim} deleted"
    db_tyre.is_deleted = True
    session.add(db_tyre)
    return {"status": "Succesfully deleted","msg": msg}