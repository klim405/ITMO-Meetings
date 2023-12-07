from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.database import init_db

init_db()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[‘’*”],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
