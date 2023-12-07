from typing import Annotated, List

from fastapi import APIRouter, Path, HTTPException, status, Query

from app.api.deps import get_current_channel_member
from app.auth.deps import CurrentUserDep
from app.database.deps import DBSessionDep
from app.database.utils import get_or_404
from app.models import Meeting, User, Feedback
from app.models.channel_member import Permission
from app.models.meeting_memeber import MeetingMember
from app.schemas.feedback import ReadFeedback, FeedbackBase
from app.schemas.meeting import ReadMeeting, CreateMeeting, UpdateMeeting
from app.schemas.user import ReadOpenUserInfo, get_open_user_info
from app.utils.time import datetime_now

router = APIRouter()


@router.get('/list/', response_model=List[ReadMeeting])
def get_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        completed: Annotated[bool, Query(description='Include completed meetings at the current time.')] = False,
        channel: Annotated[int | None, Query(description='Filter by channel')] = None,
):
    criteria = []
    if not completed:
        criteria.append(Meeting.start_datetime > datetime_now())
    if channel is not None:
        criteria.append(Meeting.channel_id == channel)
    meeting_list = Meeting.filter(db, *criteria)
    return meeting_list


@router.get('/{meeting_id}/', response_model=ReadMeeting)
def get_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.SEE_MEETINGS)
    return meeting


@router.post('/', response_model=ReadMeeting)
def create_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        creating_data: CreateMeeting
):
    curr_member = get_current_channel_member(db, curr_user_info, creating_data.channel_id)
    curr_member.has_permission_or_403(Permission.CREATE_MEETING)
    meeting = Meeting.create(db, creating_data)
    return meeting


@router.put('/{meeting_id}/', response_model=ReadMeeting)
def update_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)],
        updating_data: UpdateMeeting
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.UPDATE_MEETING)
    meeting.update(db, updating_data)
    return meeting


@router.delete('/{meeting_id}/')
def delete_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.DELETE_MEETING)
    meeting.delete(db)


@router.post('/{meeting_id}/member/', tags=['meeting member'])
def join_to_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.JOIN_TO_MEETING)
    if len(meeting.members) >= meeting.capacity:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Capacity is full'
        )
    meeting.members.append(curr_member.user)
    meeting.save(db)


@router.delete('/{meeting_id}/member/me/', tags=['meeting member'])
def leave_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    user = curr_user_info.get_model(db)
    if user not in meeting.members:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='You are not meeting member'
        )
    meeting.members.remove(user)
    meeting.save(db)


@router.delete('/{meeting_id}/member/{member_id}/', tags=['meeting member'])
def kick_channel_member(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)],
        member_id: Annotated[int, Path(ge=1, description='This is User.id')]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.UPDATE_MEETING)
    kicked_user = get_or_404(User, db, id=member_id)
    meeting.members.remove(kicked_user)
    meeting.save(db)


@router.get('/{meeting_id}/member/list/', tags=['meeting member'],
            response_model=List[ReadOpenUserInfo])
def get_member_list(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.SEE_MEETINGS_MEMBERS)
    return map(get_open_user_info, meeting.members)


@router.get('/{meeting_id}/feedback/', tags=['meeting feedback'], response_model=ReadFeedback)
def get_feedback(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    return get_or_404(Feedback, db, meeting_id=meeting_id, user_id=curr_user_info.id)


@router.post(
    '/{meeting_id}/feedback/',
    tags=['meeting feedback'],
    description="Add feedback to target meeting. "
                "If current time is less than meeting start time, then server will return HTTP 409.",
    response_model=ReadFeedback
)
def create_feedback(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)],
        creating_data: FeedbackBase
):
    meeting_member = get_or_404(MeetingMember, db, user_id=curr_user_info.id, meeting_id=meeting_id)
    if meeting_member.meeting.start_time > datetime_now():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='The meeting has not passed yet.'
        )
    feedback = Feedback(
        user_id=curr_user_info.id,
        meeting_id=meeting_id,
        rate=creating_data.rate
    )
    feedback.save(db)
    return feedback


@router.put('/{meeting_id}/feedback/', tags=['meeting feedback'], response_model=ReadFeedback)
def update_feedback(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)],
        updating_data: FeedbackBase
):
    feedback = get_or_404(Feedback, db, meeting_id=meeting_id, user_id=curr_user_info.id)
    feedback.update(db, updating_data)
    return feedback


@router.delete('/{meeting_id}/feedback/', tags=['meeting feedback'])
def delete_feedback(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    feedback = get_or_404(Feedback, db, meeting_id=meeting_id, user_id=curr_user_info.id)
    feedback.delete(db)
