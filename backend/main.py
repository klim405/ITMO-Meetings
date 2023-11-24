from fastapi import FastAPI

from app.api import api_router
from app.database import init_db

init_db()

app = FastAPI()
app.include_router(api_router)
