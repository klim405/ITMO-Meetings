from fastapi import APIRouter

from app.api.endpoints import channel, meeting, security, user

api_router = APIRouter()
api_router.include_router(user.router, tags=["Пользователи (users)"], prefix="/user")
api_router.include_router(channel.router, tags=["Сообщества (channels)"], prefix="/channel")
api_router.include_router(meeting.router, tags=["Мероприятия (meetings)"], prefix="/meeting")
api_router.include_router(security.router, tags=["Безопасность (security)"], prefix="/auth")
