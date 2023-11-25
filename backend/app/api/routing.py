from fastapi import APIRouter

from app import auth
from app.api.endpoints import user, channel, meeting

api_router = APIRouter()
api_router.include_router(user.router, tags=['user'], prefix='/user')
api_router.include_router(channel.router, tags=['channel'], prefix='/channel')
api_router.include_router(meeting.router, tags=['meeting'], prefix='/meeting')
api_router.include_router(auth.router, tags=['security'], prefix='/auth')