from fastapi import FastAPI
from .app_info import description

app = FastAPI(
    description= description
)

