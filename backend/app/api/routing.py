from fastapi import APIRouter

from app import auth
from app.api.endpoints import user, channel, meeting

api_router = APIRouter()
api_router.include_router(user.router, tags=['Пользователи (users)'], prefix='/user')
api_router.include_router(channel.router, tags=['Сообщества (channels)'], prefix='/channel')
api_router.include_router(meeting.router, tags=['Мероприятия (meetings)'], prefix='/meeting')
api_router.include_router(auth.router, tags=['Безопасность (security)'], prefix='/auth')
