import uuid
from functools import wraps

from flask import request, g

from app.api.exceptions import UnauthorizedAPIError, PermissionAPIError, ObjectNotFoundAPIError
from app.models.models import AuthToken, ChannelMember, Channel


def login_required(func):
    """ Декоратор проверяет токен пользователя:
        :raises UnauthorizedAPIError при ошибке аутентификации """
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
            if not auth_token.user.is_active:
                raise UnauthorizedAPIError({'user_inactive_error': 'Пользователь деактивирован'})
            g.current_user = auth_token.user
        except KeyError:
            raise UnauthorizedAPIError({'token_error': 'Нет заголовка "Authorization" в запросе'})
        except ValueError:
            raise UnauthorizedAPIError({'token_format_error': 'Некорректный формат токена'})
        return func(*args, **kwargs)
    return decorator


@login_required
def staff_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if g.current_user.is_staff:
            return func(*args, **kwargs)
        raise PermissionAPIError()


def channel_mixin(func):
    """ Декоратор. Извлекает из url channel_id (1 аргумент).
        Создает глобальную переменную g.channel с текущим объектом канала.
        Создает глобальную переменную g.current_member,
        если пользователь является подписчиком данного канала, иначе None"""
    @wraps(func)
    def wrapper(channel_id, *args, **kwargs):
        g.channel = Channel.get(channel_id)
        if g.channel is None:
            raise ObjectNotFoundAPIError()
        g.current_member = ChannelMember.get(g.current_user, g.channel)
        return func(*args, **kwargs)
    return wrapper


def has_member_permission(perms, permission):
    """ Проверяет есть ли право permission в правах perms """
    return bool(perms & permission)


def member_permission_required(permission):
    """ Проверяет права подписчика, отправившего запрос,
        для корректной работы необходимо использовать декораторы login_required, channel_mixin.
        :param permission необходимое право
        :raise PermissionAPIError при отсутствии требуемых прав"""
    if g.current_member is None:
        member_permissions = g.channel.get_guest_permissions()
    else:
        member_permissions = g.current_member.permissions
    if member_permissions & permission != permission:
        raise PermissionAPIError()
