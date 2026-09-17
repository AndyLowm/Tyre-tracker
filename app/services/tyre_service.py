from sqlmodel import Session
from app.models.database import TyreCreate, Tyre, TyreLocation
from sqlmodel import select

def tyre_duplicate_check(session: Session, payload: TyreCreate)-> bool:
    """ Checks if tyres exists in database"""
    duplicate_check = session.exec(
    select(Tyre).where(
        Tyre.make == payload.make,
        Tyre.model == payload.model,
        Tyre.width == payload.width,
        Tyre.aspect_ratio == payload.aspect_ratio,
        Tyre.rim == payload.rim,
        Tyre.speed_rating == payload.speed_rating
    )
    ).first()
    return bool(duplicate_check)

def create_db_tyre(payload: TyreCreate)-> Tyre:
    """ Creates and returns Tyre model instance """
    total_stock = payload.stock_unit + payload.stock_van    
    tyre_dict = payload.model_dump(exclude={"stock_van", "stock_unit"})
    tyre_dict["stock_total"] = total_stock
    return Tyre(**tyre_dict)

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