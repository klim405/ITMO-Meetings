import uuid
from functools import wraps

from flask import request, g

from app.api.exceptions import UnauthorizedAPIError
from app.models.models import AuthToken


def login_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            auth = request.headers['Authorization']
            token_type, token = auth.strip().split()
            if token_type.lower() != 'bearer':
                raise UnauthorizedAPIError(
                    {'token_type_error': 'Неверный тип токена. Корректный формат "Bearer <токен>"'})
            auth_token = AuthToken.get(uuid.UUID(token))
            if auth_token is None or not auth_token.is_active():
                raise UnauthorizedAPIError({'token_expired_error': 'Срок годности токена истек'})
            if auth_token.user.is_active:
                raise UnauthorizedAPIError({'user_inactive_error': 'Пользователь деактивирован'})
            g.current_user = auth_token.user
        except KeyError:
            raise UnauthorizedAPIError({'token_error': 'Нет токена'})
        except ValueError:
            raise UnauthorizedAPIError({'token_format_error': 'Некорректный формат токена'})
        return func(*args, **kwargs)
    return decorator
