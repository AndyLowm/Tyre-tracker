from sqlmodel import Session
from app import schemas
from app import models
from sqlmodel import select
from sqlalchemy.orm import contains_eager
from app.dependencies.config import logger
from typing import TypedDict

# =======================================================
# VALIDATION CHECKS
# =======================================================
class CpCalcDict(TypedDict, total=False):
    old_stock: int
    new_stock: int
    new_cost: float
    old_cost: float
    total: int

def get_tyre_data(session: Session, payload: schemas.TyreBase)-> models.Tyre | None:
    """ Returns Tyre data if exisits in database  """
    duplicate_check = session.exec(
    select(models.Tyre).where(
        models.Tyre.make == payload.make,
        models.Tyre.model == payload.model,
        models.Tyre.width == payload.width,
        models.Tyre.aspect_ratio == payload.aspect_ratio,
        models.Tyre.rim == payload.rim,
        models.Tyre.speed_rating == payload.speed_rating,
    )
    ).first()
    return duplicate_check


def get_or_create_tyre_entry( session: Session, payload: schemas.TyreBase) -> models.Tyre:
    """ If tyre doesnt exist, creates it and flushes database """
    tyre = get_tyre_data(session, payload)
    if not tyre:
        tyre_data = models.Tyre(**payload.model_dump())
        session.add(tyre_data)
        session.flush()
    else:
        tyre_data = tyre
    return tyre_data


def create_cp_dict(
    old_stock: int, 
    new_location_stock: dict[str,int],
    new_cost_price: float,
    old_cost_price: float
    )-> CpCalcDict:
    """ Creates cost price dict for calculations """
    old_stock_total = old_stock
    new_stock_total = sum(new_location_stock.values())
    cp_calc = {
        "old_stock": old_stock_total,
        "new_stock": new_stock_total,
        "new_cost": new_cost_price,
        "old_cost": old_cost_price,
        "total": old_stock_total + new_stock_total
        }
    return cp_calc


def create_tyre_confirm_model(
    tyre_data: models.Tyre,
    cost_price: float,
    stock_total: int
)-> schemas.TyreCreateConfirm:
    """ Creates a tyre cofirmation model """
    tyre_confirm = tyre_data.model_dump(exclude={"id", "stocks"})
    tyre_confirm["tyre_id"] = tyre_data.id
    tyre_confirm["cost_price"] = cost_price
    tyre_confirm["stock_total"] = stock_total
    return schemas.TyreCreateConfirm(**tyre_confirm)


def get_account_price(session: Session, acc_id: int, tyre_id: int)-> models.AccountPrices | None:
    """ Gets account prices model with matching acc_id and tyre_id """
    account_p = session.exec(
        select(models.AccountPrices)
        .where(models.AccountPrices.tyre_id == tyre_id)
        .where(models.AccountPrices.acc_id == acc_id)
        .with_for_update()
        ).first()
    return account_p


def create_and_update_stock_location_rows(
    session: Session, 
    tyre_id: int, 
    acc_id: int, 
    location_stock: dict[str,int]
    )-> None:
    """ Creates and updates stock amount rows in StockLocation table """
    locked_stocks = session.exec(
        select(models.StockLocation)
        .where(models.StockLocation.tyre_id == tyre_id)
        .where(models.StockLocation.acc_id == acc_id)
        .with_for_update()
        ).all()
    existing_stock = {s.location_name: s for s in locked_stocks}
    for loc, amount in location_stock.items():
        if loc in existing_stock:
            existing_stock[loc].amount += amount
            session.add(existing_stock[loc])
        else:
            new_loc_row = models.StockLocation(
                tyre_id= tyre_id,
                acc_id= acc_id,
                location_name= loc,
                amount= amount
            )
            session.add(new_loc_row)
    return


def create_or_update_account_price(
     session: Session, 
    acc_id: int,
    tyre_id: int,
    new_cost_price: float,
    new_location_stock: dict[str,int],
    old_stock_total: int
    )-> models.AccountPrices:
    """ Checks if the account price record exists, or creates it and returns updated account price record """
    account_p = get_account_price(session, acc_id, tyre_id)
    if not account_p:
        updated_account_p = models.AccountPrices(
            tyre_id= tyre_id,
            acc_id= acc_id,
            cost_price= new_cost_price
        )
        session.add(updated_account_p)
    else:
        cp_dict = create_cp_dict(old_stock_total, new_location_stock, new_cost_price, account_p.cost_price)
        account_p.cost_price = calc_new_cost_price(cp_dict)
        updated_account_p = account_p
        session.add(updated_account_p)
    return updated_account_p


def calc_new_cost_price(cp_dict: CpCalcDict):
        """Calculates new weighted cost price of tyre """
        new_stock = cp_dict['new_cost'] * cp_dict['new_stock']
        old_stock = cp_dict['old_cost'] * cp_dict['old_stock']
        total_stock = new_stock + old_stock
        if cp_dict['total'] > 0:
            new_price = round(total_stock / cp_dict["total"], 2)
        else:
            new_price = cp_dict['old_cost']
        return new_price


def add_tyre_master( session: Session, payload: schemas.TyreCreate, acc_id: int)->schemas.TyreCreateConfirm:
    """ Master plan for adding tyre to database """
    tyre_data = get_or_create_tyre_entry(session, payload)
    old_stock_total = tyre_data.get_stock_total(acc_id)

    create_and_update_stock_location_rows(session, tyre_data.id, acc_id, payload.location_stock)

    updated_account_p = create_or_update_account_price(
        session,
        acc_id,
        tyre_data.id,
        payload.cost_price,
        payload.location_stock,
        old_stock_total
        )

    tyre_confirm = create_tyre_confirm_model(
        tyre_data,
        updated_account_p.cost_price,
        tyre_data.get_stock_total(acc_id)
    )
    return tyre_confirm


def add_tyre_stock_master(
     session: Session, 
    acc_id: int,
    tyre_data: models.Tyre,
    payload: schemas.TyreStockAdjustmentRequest
    )-> schemas.TyreInventoryPublic:
    """ Master tyre addition flow """
    old_stock_total = tyre_data.get_stock_total(acc_id)

    create_and_update_stock_location_rows(
        session, tyre_data.id, acc_id, payload.location_amount
    )
    AccountP = create_or_update_account_price(
        session, acc_id, 
        tyre_data.id, 
        payload.cost_price,payload.location_amount, 
        old_stock_total
    )
    
    public_tyre_dict = tyre_data.model_dump(exclude={"id", "stocks"}) | {"cost_price": AccountP.cost_price}
    public_tyre_dict["total_stock"] = tyre_data.get_stock_total(acc_id) 
    return schemas.TyreInventoryPublic(**public_tyre_dict)


def remove_stock_master(
     session: Session,
    payload: schemas.TyreStockAdjustment,
    acc_id: int,
    tyre_id: int
    )-> schemas.TyreStockPublic:

    locked_stocks = session.exec(
        select(models.StockLocation)
        .where(models.StockLocation.tyre_id == tyre_id)
        .where(models.StockLocation.acc_id == acc_id)
        .with_for_update()
    ).all()

    exisiting_stocks = {s.location_name: s for s in locked_stocks}
    for loc, amount in payload.location_amount.items():
        if loc not in exisiting_stocks:
            raise ValueError("Location doesnt exist")
        if amount > exisiting_stocks[loc].amount:
            raise ValueError(f"Not enough stock in {loc}")  
        exisiting_stocks[loc].amount -= amount
        session.add(exisiting_stocks[loc])

    new_stock_total = sum(s.amount for s in exisiting_stocks.values())
    new_stocks = {loc: s.amount for loc, s in exisiting_stocks.items()}
    return schemas.TyreStockPublic(stock_locations=new_stocks, total_stock=new_stock_total)


def tyre_search(
        filters: schemas.TyreSearch, 
        session: Session, 
        acc_id: int
        )-> list[dict]:
    """
    Queries the database for tyres matching the provided specification filters 
    and matches them against the account's active cost price.

    Args:
        filters (models.TyreSearch): Physical tyre dimensions and brand specs to match.
        session (Session): The active database transaction session.
        acc_id (int): The unique account ID used for pricing and inventory isolation.

    Raises:
        ValueError: If the filters object contains no active search parameters.
        LookupError: If no matching tyre or inventory assets are found.

    Returns:
        list[dict]: A flattened list of dictionaries containing full tyre specs 
                    and a 'cost_price' added to each dict.
    """
    tyre_filters = filters.model_dump(exclude_none= True)
    if not tyre_filters:
        raise ValueError("No filters found")

    statement = select(models.Tyre, models.AccountPrices.cost_price)
    statement = statement.join(models.StockLocation, models.Tyre.id == models.StockLocation.tyre_id)
    statement = statement.join(models.AccountPrices, (models.AccountPrices.tyre_id == models.StockLocation.tyre_id) & (models.AccountPrices.acc_id == models.StockLocation.acc_id))

    for key,val in tyre_filters.items():
        column = getattr(models.Tyre, key)
        statement = statement.where(column == val)
    
    statement = statement.where(models.StockLocation.acc_id == acc_id)
    statement = statement.options(contains_eager(models.Tyre.stocks))

    tyres: list[tuple[models.Tyre, float]] = session.exec(statement).unique().all()
    if not tyres:
        raise LookupError("No records found")
    tyre_list = []
    for res in tyres:
        tyre_obj, cp = res
        tyre_dict = tyre_obj.model_dump(exclude={"stocks"})
        tyre_dict["cost_price"] = cp
        tyre_list.append(tyre_dict)
    return tyre_list
    

