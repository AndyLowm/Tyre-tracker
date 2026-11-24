from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.app_info import description, title
from app.routers import tyres, views, logins
from contextlib import asynccontextmanager
from app.dependencies.database import create_db_and_tables
from app.exceptions import TyreTrackerError
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    description= description,
    title= title,
    lifespan=lifespan
)

@app.exception_handler(TyreTrackerError)
async def tyre_tracker_error_handler(request: Request, exc: TyreTrackerError) -> JSONResponse:
    return JSONResponse(
        status_code= exc.status_code,
        content= {
            "detail": str(exc)
        }
    )

# Mount static files path
app.mount('/static', StaticFiles(directory='app/static'), name='static')
# Add webpage router and remove from schema
app.include_router(views.router, include_in_schema=False)
app.include_router(tyres.router)
app.include_router(logins.router)
