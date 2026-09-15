from sqlmodel import create_engine, SQLModel, Session
from fastapi import Depends
from app.dependencies.config import settings
from typing import Annotated
#databse models
from app.models import TyreLocation, Tyre

db_url = settings.database_url
conn_args = {"check_same_thread": False} if db_url.startswith('sqlite') else {}
engine = create_engine(db_url, connect_args=conn_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

Session_Dep = Annotated[Session, Depends(get_session)]