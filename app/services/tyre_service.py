from sqlmodel import Session
from app.models.tyre import (
    TyreCreate, 
    Tyre, 
    StockLocation, 
    TyreStockAdjustmentRequest, 
    TyreStockAdjustment,
    TyreBase, 
    TyreCreateConfirm, 
    AccountPrices,
    TyreInventoryPublic,
    TyreStockPublic)
from sqlmodel import select
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

class TyreService():
    """ Service layer logic for inventory """
    @staticmethod
    def get_tyre_data(session: Session, payload: TyreBase)-> Tyre | None:
        """ Returns Tyre data if exisits in database  """
        duplicate_check = session.exec(
        select(Tyre).where(
            Tyre.make == payload.make,
            Tyre.model == payload.model,
            Tyre.width == payload.width,
            Tyre.aspect_ratio == payload.aspect_ratio,
            Tyre.rim == payload.rim,
            Tyre.speed_rating == payload.speed_rating,
        )
        ).first()
        return duplicate_check
    
    @classmethod
    def get_or_create_tyre_entry(cls, session: Session, payload: TyreBase) -> Tyre:
        """ If tyre doesnt exist, creates it and flushes database """
        tyre = cls.get_tyre_data(session, payload)
        if not tyre:
            tyre_data = Tyre(**payload.model_dump())
            session.add(tyre_data)
            session.flush()
        else:
            tyre_data = tyre
        return tyre_data
    
    @staticmethod
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
    
    @staticmethod
    def create_tyre_confirm_model(
        tyre_data: Tyre,
        cost_price: float,
        stock_total: int
    )-> TyreCreateConfirm:
        """ Creates a tyre cofirmation model """
        tyre_confirm = tyre_data.model_dump(exclude={"id", "stocks"})
        tyre_confirm["tyre_id"] = tyre_data.id
        tyre_confirm["cost_price"] = cost_price
        tyre_confirm["stock_total"] = stock_total
        return TyreCreateConfirm(**tyre_confirm)
    
    @staticmethod
    def get_account_price(session: Session, acc_id: int, tyre_id: int)-> AccountPrices | None:
        """ Gets account prices model with matching acc_id and tyre_id """
        account_p = session.exec(
            select(AccountPrices)
            .where(AccountPrices.tyre_id == tyre_id)
            .where(AccountPrices.acc_id == acc_id)
            .with_for_update()
            ).first()
        return account_p

    @staticmethod
    def create_and_update_stock_location_rows(
        session: Session, 
        tyre_id: int, 
        acc_id: int, 
        location_stock: dict[str,int]
        )-> None:
        """ Creates and updates stock amount rows in StockLocation table """
        locked_stocks = session.exec(
            select(StockLocation)
            .where(StockLocation.tyre_id == tyre_id)
            .where(StockLocation.acc_id == acc_id)
            .with_for_update()
            ).all()
        existing_stock = {s.location_name: s for s in locked_stocks}
        for loc, amount in location_stock.items():
            if loc in existing_stock:
                existing_stock[loc].amount += amount
                session.add(existing_stock[loc])
            else:
                new_loc_row = StockLocation(
                    tyre_id= tyre_id,
                    acc_id= acc_id,
                    location_name= loc,
                    amount= amount
                )
                session.add(new_loc_row)
        return
    
    @classmethod
    def create_or_update_account_price(
        cls, session: Session, 
        acc_id: int,
        tyre_id: int,
        new_cost_price: float,
        new_location_stock: dict[str,int],
        old_stock_total: int
        )-> AccountPrices:
        """ Checks if the account price record exists, or creates it and returns updated account price record """
        account_p = cls.get_account_price(session, acc_id, tyre_id)
        if not account_p:
            updated_account_p = AccountPrices(
                tyre_id= tyre_id,
                acc_id= acc_id,
                cost_price= new_cost_price
            )
            session.add(updated_account_p)
        else:
            cp_dict = cls.create_cp_dict(old_stock_total, new_location_stock, new_cost_price, account_p.cost_price)
            account_p.cost_price = cls.calc_new_cost_price(cp_dict)
            updated_account_p = account_p
            session.add(updated_account_p)
        return updated_account_p
    
    @staticmethod
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
    
    @classmethod
    def add_tyre_master(cls, session: Session, payload: TyreCreate, acc_id: int)->TyreCreateConfirm:
        """ Master plan for adding tyre to database """
        tyre_data = cls.get_or_create_tyre_entry(session, payload)
        old_stock_total = tyre_data.get_stock_total(acc_id)

        cls.create_and_update_stock_location_rows(session, tyre_data.id, acc_id, payload.location_stock)

        updated_account_p = cls.create_or_update_account_price(
            session,
            acc_id,
            tyre_data.id,
            payload.cost_price,
            payload.location_stock,
            old_stock_total
            )

        tyre_confirm = cls.create_tyre_confirm_model(
            tyre_data,
            updated_account_p.cost_price,
            tyre_data.get_stock_total(acc_id)
        )
        return tyre_confirm
    
    @classmethod
    def add_tyre_stock_master(
        cls, session: Session, 
        acc_id: int,
        tyre_data: Tyre,
        payload: TyreStockAdjustmentRequest
        )-> TyreInventoryPublic:
        """ Master tyre addition flow """
        old_stock_total = tyre_data.get_stock_total(acc_id)

        cls.create_and_update_stock_location_rows(
            session, tyre_data.id, acc_id, payload.location_amount
        )
        AccountP = cls.create_or_update_account_price(
            session, acc_id, 
            tyre_data.id, 
            payload.cost_price,payload.location_amount, 
            old_stock_total
        )
        
        public_tyre_dict = tyre_data.model_dump(exclude={"id", "stocks"}) | {"cost_price": AccountP.cost_price}
        public_tyre_dict["total_stock"] = tyre_data.get_stock_total(acc_id) 
        return TyreInventoryPublic(**public_tyre_dict)
    
    @classmethod
    def remove_stock_master(
        cls, session: Session,
        payload: TyreStockAdjustment,
        acc_id: int,
        tyre_id: int
        )-> TyreStockPublic:

        locked_stocks = session.exec(
            select(StockLocation)
            .where(StockLocation.tyre_id == tyre_id)
            .where(StockLocation.acc_id == acc_id)
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
        return TyreStockPublic(stock_locations=new_stocks, total_stock=new_stock_total)
    

