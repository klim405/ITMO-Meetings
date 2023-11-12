import uuid

from flask import request, jsonify, g, abort

from app.api import api
from app.api.authentication import login_required, member_permission_required, channel_mixin
from app.api.decorators import object_view
from app.api.exceptions import ValidationAPIError, UnauthorizedAPIError, PermissionAPIError, ObjectNotFoundAPIError, \
    BadRequestAPIError, APIError
from app.api.forms import ChangePasswordForm, RegistrationUserForm, ChannelForm, MeetingForm, UpdateUserForm, \
    UpdateUserFormForStaff
from app.api.utils import jsonify_obj, jsonify_empty, jsonify_objs, user_to_json, jsonify_list
from app.models.models import User, AuthToken, AuthTokenError, Permission, Channel, ChannelMember, Meeting, Role


@api.route('/auth/login/', methods=['POST'])
def login():
    """ Представление идентификации, параметр username должен содержать значение одного из полей:
        username, email, telephone, модели User.
        :raise ValidationAPIError"""
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    user = User.get_by_login(username)
    if user is None:
        raise ValidationAPIError(data={'username': 'wrong_username'})
    if not user.verify_password(password):
        raise ValidationAPIError(data={'password': 'wrong_password'})
    if not user.is_active:
        raise BadRequestAPIError(data={'user_inactive_error': 'Пользователь деактивирован'})
    token = user.gen_auth_token()
    return jsonify(token.to_json()), 201


@api.route('/auth/refresh/', methods=['POST'])
def refresh():
    """ Выполняет обновления токена аутентификации
        :raises ValidationAPIError не верный токен,
        UnauthorizedAPIError - токен был деактивирован или уже использован."""
    try:
        refresh_token = request.json.get('refresh_token')
        old_token = AuthToken.query.filter_by(refresh_token=uuid.UUID(refresh_token)).first()
        new_token = old_token.refresh()
        return jsonify(new_token.to_json()), 201
    except (TypeError, KeyError, ValueError, AttributeError):
        raise ValidationAPIError(data={'refresh_token': 'wrong_refresh_token'})
    except AuthTokenError:
        raise UnauthorizedAPIError(data={'auth_token_error': 'Токен был уже обновлен или деактивирован'})


@api.route('/auth/logout/', methods=['POST', 'PUT'])
@login_required
def logout():
    """ Выполняет деактивацию текущего токена пользователя. """
    try:
        auth_token = AuthToken.get(uuid.UUID(request.json.get('access_token')))
        if g.current_user.is_staff or g.current_user.id == auth_token.user_id:
            auth_token.deactivate()
            auth_token.save()
            return jsonify_empty(), 200
        else:
            raise PermissionAPIError()
    except TypeError:
        raise ValidationAPIError({'access_token': 'not_null'})
    except ValueError:
        raise ValidationAPIError({'access_token': 'wrong_format'})


@api.route('/auth/logout-anywhere/', methods=['GET', 'POST'])
@login_required
def logout_anywhere():
    """ Выполняет деактивации всех токенов пользователя. """
    g.current_user.deactivate_all_auth_tokens()
    return jsonify_empty(), 200


@api.route('/auth/reset-password/', methods=['PUT'])
@login_required
def reset_password():
    password_form = ChangePasswordForm(request.json, g.current_user)
    if password_form.validate():
        user = password_form.save()
        return jsonify_obj(user), 201
    else:
        raise ValidationAPIError(data=password_form.get_errors())


@api.route('/auth/recovery-password/', methods=['POST'])
def recovery_password():
    # todo: recovery_password
    abort(404)


@api.route('/user/', methods=['GET', 'DELETE'])
@login_required
def get_current_user():
    if request.method == 'DELETE':
        g.current_user.deactivate_and_save()
        return jsonify_empty(), 200
    return user_to_json(g.current_user, ignore_confidentiality=True), 200


@api.route('/user/registrate/', methods=['POST'])
def registrate():
    form = RegistrationUserForm(request.json)
    # todo: send email
    if form.validate():
        form.save()
        return jsonify_empty(), 201
    raise ValidationAPIError(data=form.validation_errors)


@api.route('/user/<int:object_pk>/', methods=['GET', 'PUT', 'DELETE'])
@login_required
@object_view(User)
def get_user():
    if g.current_user.is_staff or g.current_user.id == g.object.id:
        if request.method == 'GET':
            return user_to_json(g.object, ignore_confidentiality=True), 200

        elif request.method == 'PUT':
            if g.current_user.is_staff:
                form = UpdateUserFormForStaff(request.json, g.object)
            else:
                form = UpdateUserForm(request.json, g.object)
            if not form.validate():
                raise ValidationAPIError(form.get_errors())
            return jsonify_obj(form.save())

        elif request.method == 'DELETE':
            g.object.deactivate_and_save()
            return jsonify_empty(), 200

    # Для людей не имеющие доступ к редактированию и просмотра конфиденциальной информации
    elif request.method == 'GET':
        return user_to_json(g.object), 200
    raise PermissionAPIError()


@api.route('/user/list/', methods=['GET'])
@login_required
def user_list():
    # todo: user list
    pass


@api.route('/channel/list/', methods=['GET'])
@login_required
def channel_list():
    # todo: check paginator
    # todo: make filter
    try:
        page = request.args.get('p', '1', type=int)
        # todo: make constant FLASKY_POSTS_PER_PAGE
        pagination = Channel.query.order_by(Channel.rating).paginate(
            page, per_page=10, error_out=False
        )
        return jsonify_list(pagination), 200
    except ValueError:
        raise ValidationAPIError({'p': 'wrong_page'})


@api.route('/channel/', methods=['POST'])
@login_required
def create_channel():
    channel_form = ChannelForm(request.json)
    if not channel_form.validate():
        raise ValidationAPIError(channel_form.get_errors())
    channel = channel_form.save()
    channel.add_member(g.current_user, Role.OWNER)
    return jsonify_obj(channel), 201


@api.route('/channel/<int:channel_id>/', methods=['GET', 'PUT', 'DELETE'])
@login_required
@channel_mixin
def channel_view():
    if request.method == 'GET':
        return jsonify_obj(g.channel), 200

    elif request.method == 'PUT':
        member_permission_required(Permission.UPDATE_CHANNEL)
        channel_form = ChannelForm(request.json, g.channel)
        if not channel_form.validate():
            raise ValidationAPIError(channel_form.get_errors())
        channel = channel_form.save()
        return jsonify_obj(channel), 200

    elif request.method == 'DELETE':
        member_permission_required(Permission.DELETE_CHANNEL)
        g.channel.delete()
        return jsonify_empty(), 200


@api.route('/channel/personal/', methods=['GET', 'PUT'])
@login_required
def personal_channel():
    if request.method == 'GET':
        try:
            owner_channel_member = list(filter(
                lambda cm: cm.channel.is_personal and cm.has_permissions(Permission.IS_OWNER),
                g.current_user.channel_members
            ))
            return jsonify_obj(owner_channel_member[0].channel), 200
        except IndexError:
            return APIError({'server_error': 'Пользователь не имеет своего канала.'})


@api.route('/channel/member/roles/', methods=['GET'])
@login_required
def channel_member_roles():
    """ Возвращает список возможных ролей участников канала. """
    return jsonify(Role.to_json()), 200


@api.route('/channel/<int:channel_id>/leave/')
@login_required
@channel_mixin
def leave_channel():
    if g.current_member is None:
        raise ObjectNotFoundAPIError()
    if g.current_member.has_permission(Permission.IS_OWNER):
        if g.channel.is_personal:
            raise PermissionAPIError()
        if g.channel.members_cnt == 1:
            g.channel.delete()
            return jsonify_empty(), 200
        new_owner = g.channel.channel_members.order_by(ChannelMember.permissions).first()
        new_owner.permissions = Role.OWNER
        new_owner.save()
    g.current_member.delete()
    return jsonify_empty(), 200


@api.route('/channel/<int:channel_id>/member/list/', methods=['GET'])
@login_required
@channel_mixin
def channel_member_list():
    member_permission_required(Permission.SEE_MEMBERS)
    return jsonify_objs(g.channel.channel_members), 200


@api.route('/channel/<int:channel_id>/member/<int:user_id>/permissions/', methods=['PUT'])
@login_required
@channel_mixin
def set_permissions_to_channel_member(user_id):
    """ Устанавливает права подписчика, установить права может только пользователь,
        имеющий право Permission.GIVE_ACCESS. Пользователь может наделить другого пользователя правами,
        которыми он сам владеет.
        :raises ObjectNotFoundAPIError участник не найден,
        ValidationAPIError неверный формат прав
        PermissionAPIError недостаточно прав доступа для наделения правами другого участника"""
    member_permission_required(Permission.GIVE_ACCESS)
    channel_member = ChannelMember.get(user_id, g.channel)
    if channel_member is None:
        raise ObjectNotFoundAPIError()

    new_perm = request.json.get('permissions', None, type=int)
    if new_perm is None:
        raise ValidationAPIError({'permissions': 'not_null'})

    # если пользователь дает права которыми не владеет другому пользователю -> ошибка
    # если пользователь изменяет права владельца -> ошибка
    # если пользователь изменяет свои права -> ошибка
    if g.current_member.permissions & new_perm != new_perm or channel_member.has_permission(Permission.IS_OWNER) \
            or channel_member.user.id == g.current_user.id:
        raise PermissionAPIError()

    # если передается право владельца
    if new_perm & Permission.IS_OWNER:
        g.current_member.permissions = Role.ADMIN
        g.current_member.save()

    channel_member.permissions = new_perm
    channel_member.save()

    return jsonify_empty(), 200


@api.route('/channel/<int:channel_id>/meeting/<int:meeting_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@channel_mixin
@object_view(Meeting)
def meeting():
    if request.method == 'GET':
        member_permission_required(Permission.SEE_MEETING)
        return jsonify_obj(g.object), 200

    elif request.method == 'PUT':
        member_permission_required(Permission.UPDATE_MEETING)
        channel_form = MeetingForm(request.json, g.object)
        if not channel_form.validate():
            raise ValidationAPIError(channel_form.get_errors())
        channel = channel_form.save()
        return jsonify_obj(channel), 200

    elif request.method == 'DELETE':
        member_permission_required(Permission.UPDATE_MEETING)
        g.object.delete()
        return jsonify_empty(), 200


@api.route('/channel/<int:channel_id>/meeting/list', methods=['GET'])
@login_required
@channel_mixin
def channel_meeting_list():
    # todo:
    pass
