from flask import jsonify, Response

from app.models.mixins import DBModelAPIMixin
from app.models.models import User, ALL_CONFIDENTIALITY
from app.models.models import Confidentiality as Conf


def jsonify_empty() -> Response:
    """ Возвращает пустой json ответ с пустым словарём. """
    return jsonify({})


def jsonify_obj(obj: DBModelAPIMixin) -> Response:
    """ Возвращает json ответ с объектом. """
    return jsonify({'object': obj.to_json()})


def jsonify_objs(objs) -> Response:
    """ Возвращает json ответ со списком объектов. """
    return jsonify({'list': [o.to_json() for o in objs]})


def jsonify_list(pagination):
    """ Возвращает json ответ со списком объектов и с информацией о пагинаторе """
    json_data = {
        'objects': [c.to_json() for c in pagination.items],
        'paginator': {'pages': pagination.pages,
                      'has_next': pagination.has_next}
    }
    return jsonify(json_data)


def user_to_json(u: User, add_conf=0, ignore_confidentiality=False) -> Response:
    """ Возвращает json ответ c данными о пользователе (user) на основе настроек конфиденциальности. """
    conf = u.confidentiality | add_conf
    if ignore_confidentiality:
        conf = ALL_CONFIDENTIALITY
    json_data = {
        'id': u.id,
        'username': u.username if conf & Conf.SHOW_USERNAME else None,
        'referrer_id': u.referrer_id,
        'firstname': u.firstname,
        'patronymic': u.patronymic if conf & Conf.SHOW_PATRONYMIC else None,
        'surname': u.surname if conf & Conf.SHOW_SURNAME else None,
        'other_names': u.firstname if conf & Conf.SHOW_PATRONYMIC else None,
        'sex': u.sex.value,
        'age': u.age if conf & Conf.SHOW_AGE else None,
        'telephone': u.telephone if conf & Conf.SHOW_TELEPHONE else None,
        'email': u.email if conf & Conf.SHOW_EMAIL else None,
        'confidentiality': u.confidentiality,
        'is_active': u.is_active,
        'is_staff': u.is_staff,
        'favorite_categories': [c.to_json() for c in u.favorite_categories] if conf & Conf.SHOW_CATEGORIES else None
    }
    return jsonify({'object': json_data})
