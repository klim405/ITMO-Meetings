import uuid

from flask import request, jsonify, g

from app.api import api
from app.api.authentication import login_required
from app.api.exceptions import ValidationAPIError, UnauthorizedAPIError
from app.models.models import User, AuthToken, AuthTokenError


@api.route('/auth/login/', methods=['POST'])
def login():
    username = request.form.get('username', None)
    password = request.form.get('password', None)
    user = User.get_by_login(username)
    if user is None:
        raise ValidationAPIError(data={'username': 'wrong_username'})
    if not user.verify_password(password):
        raise ValidationAPIError(data={'password': 'wrong_password'})
    token = user.gen_auth_token()
    return jsonify(token.to_json()), 201


@api.route('/auth/refresh/', methods=['POST'])
def refresh():
    try:
        refresh_token = request.form.get('refresh_token')
        old_token = AuthToken.query.filter_by(refresh_token=uuid.UUID(refresh_token)).first()
        new_token = old_token.refresh()
        return new_token.to_json()
    except (KeyError, ValueError, AttributeError):
        raise ValidationAPIError({'refresh_token': 'wrong_refresh_token'})
    except AuthTokenError:
        raise UnauthorizedAPIError({'auth_token_error': 'Токен был уже обновлен или деактивирован'})


@api.route('/auth/logout-anywhere/')
@login_required
def logout():
    g.current_user.deactivate_all_auth_tokens()
    return jsonify({}), 200


@api.route('/auth/reset-password/')
@login_required
def reset_password():
    pass


@api.route('/')


@api.route('/userlist/')
def f():
    return map(lambda x: x.username, User.query.all())