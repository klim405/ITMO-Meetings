from typing import Annotated, List

from fastapi import APIRouter, Path, HTTPException, status

from app.api.deps import get_current_channel_member
from app.auth.deps import CurrentUserDep
from app.database.deps import DBSessionDep
from app.database.utils import get_or_404
from app.models import Meeting
from app.models.channel_member import Permission
from app.schemas.meeting import ReadMeeting, CreateMeeting, UpdateMeeting
from app.schemas.user import ReadOpenUserInfo, get_open_user_info

router = APIRouter()


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


@router.post('/{meeting_id}/join/')
def delete_meeting(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.JOIN_TO_MEETING)
    if len(meeting.members) >= meeting.capacity:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Capacity is full')
    meeting.members.append(curr_member.user)
    meeting.save(db)


@router.get('/{meeting_id}/member/list/', response_model=List[ReadOpenUserInfo])
def get_member_list(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        meeting_id: Annotated[int, Path(ge=1)]
):
    meeting = get_or_404(Meeting, db, id=meeting_id)
    curr_member = get_current_channel_member(db, curr_user_info, meeting.channel_id)
    curr_member.has_permission_or_403(Permission.SEE_MEETINGS_MEMBERS)
    return map(get_open_user_info, meeting.members)


