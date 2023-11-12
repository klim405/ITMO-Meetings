from functools import wraps

from flask import g

from app import db
from app.api.exceptions import ObjectNotFoundAPIError


def object_view(model_cls):
    """ Декоратор. Создает переменную g.object с найденным объектом модели по переданному id через url."""
    def decorator(func):
        @wraps(func)
        def wrapper(object_pk, *args, **kwargs):
            g.object = db.session.get(model_cls, object_pk)
            if g.object is None:
                raise ObjectNotFoundAPIError()
            return func(*args, **kwargs)
        return wrapper
    return decorator

