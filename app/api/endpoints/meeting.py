from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.api.deps import get_current_channel_member
from app.auth.deps import CurrentUserDep
from app.database.deps import DBSessionDep
from app.database.utils import get_or_404
from app.models import Feedback, Meeting, User
from app.models.channel_member import ChannelMember, Permission, Role
from app.models.meeting_memeber import MeetingMember
from app.schemas.feedback import FeedbackBase, ReadFeedback
from app.schemas.meeting import CreateMeeting, ReadMeeting, UpdateMeeting
from app.schemas.user import ReadUser
from app.utils.time import datetime_now

router = APIRouter()


@router.get(
    "/list/",
    name="Получить список мероприятий",
    description="Возвращает все мероприятия удовлетворяющие условиям. "
    "По умолчанию возвращает все мероприятия, которые будут в будущем "
    "и которые принадлежат открытым сообществам или сообществам, "
    "в которых текущий пользователь является участником. Если текущий пользователь администратор, "
    "то возвращается все мероприятия которые будут в будущем."
    "Если нет мероприятий удовлетворяющих критериям поиска, возвращает пустой список.",
    response_model=List[ReadMeeting],
)
def get_meeting(
    db: DBSessionDep,
    curr_user_info: CurrentUserDep,
    completed: Annotated[
        bool, Query(description="Вернуть завершенные мероприятия на текущий момент.")
    ] = False,
    channel: Annotated[int | None, Query(description="Отсортировать мероприятия по каналу.")] = None,
):
    criteria = []
    if not completed:
        criteria.append(Meeting.start_datetime > datetime_now())
    if channel is not None:
        criteria.append(Meeting.channel_id == channel)
    if not curr_user_info.is_staff:
        curr_user_channel_ids = map(
            lambda cm: cm.channel.members,
            ChannelMember.filter(
                db,
                ChannelMember.user_id == curr_user_info.id,
                ChannelMember.permissions != Role.CONFIRM_WAITER,
            ),
        )
        criteria.append(Meeting.channel.has(is_public=True) | (Meeting.channel_id in curr_user_channel_ids))
    meeting_list = Meeting.filter(db, *criteria)
    return meeting_list


@router.get(
    "/{meeting_id}/",
    name="Получить мероприятие",
    description="Возвращает объект мероприятия по указанному идентификатору.",
    response_model=ReadMeeting,
)
def get_meeting(  # noqa: F811
    db: DBSessionDep, curr_user_info: CurrentUserDep, meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.SEE_MEETINGS)
    return meeting


@router.post(
    "/",
    name="Создать мероприятие",
    description="Создает мероприятие. "
    "Если авторизованный (текущий) пользователь не является участником сообщества, "
    "либо у него нет прав доступа на создание мероприятия, то возвращается HTTP 403 (Отказано в доступе)",
    response_model=ReadMeeting,
)
def create_meeting(db: DBSessionDep, curr_user_info: CurrentUserDep, creating_data: CreateMeeting):
    curr_member = get_current_channel_member(db, curr_user_info, creating_data.channel_id)
    curr_member.has_permission_or_403(Permission.CREATE_MEETING)
    meeting = Meeting.create(db, creating_data)
    return meeting


@router.put(
    "/{meeting_id}/",
    name="Изменить мероприятие",
    description="Изменяет мероприятие с указанным индексом (первичным ключом). "
    "Если авторизованный (текущий) пользователь не является участником сообщества, "
    "либо у него нет прав доступа на изменение мероприятия, то возвращается HTTP 403 (Отказано в доступе)",
    response_model=ReadMeeting,
)
def update_meeting(
    db: DBSessionDep,
    curr_user_info: CurrentUserDep,
    meeting_id: Annotated[int, Path(ge=1)],
    updating_data: UpdateMeeting,
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.UPDATE_MEETING)
    meeting.update(db, updating_data)
    return meeting


@router.delete(
    "/{meeting_id}/",
    name="Удалить мероприятие",
    description="Удаляет мероприятие без возможности восстановления.",
)
def delete_meeting(db: DBSessionDep, curr_user_info: CurrentUserDep, meeting_id: Annotated[int, Path(ge=1)]):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.DELETE_MEETING)
    meeting.delete(db)


@router.post(
    "/{meeting_id}/member/",
    name="Присоединится к мероприятию",
    description="Присоединяет к мероприятию авторизованного (текущего) пользователя. "
    "Если текущий пользователь уже добавлен, возвращает HTTP 409 (Конфликт)."
    "Если текущий пользователь не имеет прав доступа на вступление, либо количество участников максимально "
    "(т. е. нет мест), возвращает HTTP 403 (Отказано в доступе).",
    tags=["Участник мероприятия (meeting member)"],
)
def join_to_meeting(db: DBSessionDep, curr_user_info: CurrentUserDep, meeting_id: Annotated[int, Path(ge=1)]):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.JOIN_TO_MEETING)
    if len(meeting.members) >= meeting.capacity:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capacity is full")
    meeting.members.append(curr_member.user)
    meeting.save(db)


@router.get(
    "/{meeting_id}/member/list/",
    name="Возвращает данные об участниках мероприятия",
    description="Возвращает данные об участниках мероприятия, "
    "данный метод похож на метод возвращающий список пользователей, "
    "однако в данном методе значения конфиденциальных полей не скрываются. "
    "Если текущий пользователь не имеет прав на просмотр участников, "
    "возвращается HTTP 403 (Отказано в доступе).",
    tags=["Участник мероприятия (meeting member)"],
    response_model=List[ReadUser],
)
def get_meeting_members(
    db: DBSessionDep, curr_user_info: CurrentUserDep, meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.SEE_MEETINGS_MEMBERS)
    return meeting.members


@router.delete(
    "/{meeting_id}/member/me/",
    name="Покинуть мероприятие",
    description="Исключает текущего пользователя из списка участников целевого мероприятия. "
    "Метод ничего не возвращает.",
    tags=["Участник мероприятия (meeting member)"],
)
def leave_meeting(db: DBSessionDep, curr_user_info: CurrentUserDep, meeting_id: Annotated[int, Path(ge=1)]):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    user = curr_user_info.get_model(db)
    if user not in meeting.members:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not meeting member")
    meeting.members.remove(user)
    meeting.save(db)


@router.delete(
    "/{meeting_id}/member/{member_id}/",
    name="Выгнать участника мероприятия",
    description="Исключает указанного пользователя из списка участников целевого мероприятия. "
    "Если текущий пользователь пользователь не имеет права на обновление мероприятия, "
    "то возвращается  РЕЕЗ 403 (Отказано в доступе). Метод не возвращает данных.",
    tags=["Участник мероприятия (meeting member)"],
)
def kick_channel_member(
    db: DBSessionDep,
    curr_user_info: CurrentUserDep,
    meeting_id: Annotated[int, Path(ge=1)],
    member_id: Annotated[int, Path(ge=1, description="This is User.id")],
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.UPDATE_MEETING)
    kicked_user = get_or_404(User, db, id=member_id)
    meeting.members.remove(kicked_user)
    meeting.save(db)


@router.get(
    "/{meeting_id}/feedback/",
    name="Получить отзыв",
    description="Возвращает объект отзыва текущего пользователя для целевого мероприятия. "
    "Если пользователь не создавал отзыв, то возвращается HTTP 404 (Объект не найден).",
    tags=["Отзывы мероприятий (meeting feedbacks)"],
    response_model=ReadFeedback,
)
def get_feedback(db: DBSessionDep, curr_user_info: CurrentUserDep, meeting_id: Annotated[int, Path(ge=1)]):
    return get_or_404(Feedback, db, meeting_id=meeting_id, user_id=curr_user_info.id)


@router.post(
    "/{meeting_id}/feedback/",
    name="Создать отзыв",
    description="Создает отзыв от имени текущего пользователя для целевого мероприятия. "
    "Если отзыв создается до времени начала мероприятия, то возвращается HTTP 409 (Конфликт).",
    tags=["Отзывы мероприятий (meeting feedbacks)"],
    response_model=ReadFeedback,
)
def create_feedback(
    db: DBSessionDep,
    curr_user_info: CurrentUserDep,
    meeting_id: Annotated[int, Path(ge=1)],
    creating_data: FeedbackBase,
):
    meeting_member = get_or_404(MeetingMember, db, user_id=curr_user_info.id, meeting_id=meeting_id)
    if meeting_member.meeting.start_time > datetime_now():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The meeting has not passed yet.")
    feedback = Feedback(user_id=curr_user_info.id, meeting_id=meeting_id, rate=creating_data.rate)
    feedback.save(db)
    return feedback


@router.put(
    "/{meeting_id}/feedback/",
    name="Изменить отзыв",
    description="Изменяет отзыв, написанный текущим пользователем на целевое мероприятие. "
    "Если отзыва не существует, то возвращается HTTP 404 (Объект не найден).",
    tags=["Отзывы мероприятий (meeting feedbacks)"],
    response_model=ReadFeedback,
)
def update_feedback(
    db: DBSessionDep,
    curr_user_info: CurrentUserDep,
    meeting_id: Annotated[int, Path(ge=1)],
    updating_data: FeedbackBase,
):
    feedback = get_or_404(Feedback, db, meeting_id=meeting_id, user_id=curr_user_info.id)
    feedback.update(db, updating_data)
    return feedback


@router.delete(
    "/{meeting_id}/feedback/",
    name="Удалить отзыв",
    description="Удаляет отзыв, написанный текущим пользователем на целевое мероприятие. "
    "Если отзыва не существует, то возвращается HTTP 404 (Объект не найден).",
    tags=["Отзывы мероприятий (meeting feedbacks)"],
)
def delete_feedback(db: DBSessionDep, curr_user_info: CurrentUserDep, meeting_id: Annotated[int, Path(ge=1)]):
    feedback = get_or_404(Feedback, db, meeting_id=meeting_id, user_id=curr_user_info.id)
    feedback.delete(db)
