from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.app_info import description, title
from app.routers import tyres, views
from contextlib import asynccontextmanager
from app.dependencies.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    description= description,
    title= title,
    lifespan=lifespan
)


# Mount static files path
app.mount('/static', StaticFiles(directory='app/static'), name='static')
# Add webpage router and remove from schema
app.include_router(views.router, include_in_schema=False)
app.include_router(tyres.router)
