from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.app_info import description, title
from app.routers import views

app = FastAPI(
    description= description,
    title= title
)

# Mount static files path
app.mount('/static', StaticFiles(directory='app/static'), name='static')
# Add webpage router and remove from schema
app.include_router(views.router, include_in_schema=False)

