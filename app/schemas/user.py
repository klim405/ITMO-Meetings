from datetime import date
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber

from app.models.user import DEFAULT_CONFIDENTIALITY, Gender, User
from app.schemas.validators import age_validator

MIN_USER_AGE = 16


class UserPhoneNumber(PhoneNumber):
    phone_format: str = "INTERNATIONAL"


class UserBase(BaseModel):
    username: str | None = Field(
        default=None, min_length=3, max_length=20, pattern=r"^\w+$", examples=["elison98"]
    )
    telephone: UserPhoneNumber = Field(examples=["+79001234567"])
    email: EmailStr = Field(max_length=320, examples=["elison@example.com"])

    firstname: str = Field(max_length=20, pattern=r"^[А-ЯA-Z][а-яa-z]+$", examples=["Elison"])
    patronymic: str | None = Field(
        default=None, max_length=20, pattern=r"^[А-ЯA-Z][а-яa-z]+$", examples=[None]
    )
    surname: str = Field(max_length=20, pattern=r"^[А-ЯA-Z][а-яa-z]+$", examples=["Argent"])
    other_names: str | None = Field(
        default=None, max_length=256, pattern=r"^[А-Яа-яA-Za-z\s]+$", examples=[None]
    )
    gender: Gender
    date_of_birth: Annotated[
        date, AfterValidator(age_validator(MIN_USER_AGE)), Field(examples=["2000-01-01"])
    ]


class CreateUser(UserBase):
    password: str = Field(min_length=8, max_length=30, examples=["12345678"])


class UpdateUser(UserBase):
    pass


class ChangeUserPassword(BaseModel):
    password: str = Field(min_length=8, max_length=30)


class ReadUser(UserBase):
    id: int
    referrer_id: int | None = None
    confidentiality: int = DEFAULT_CONFIDENTIALITY
    is_staff: bool = False
    is_email_verified: bool

    class Config:
        from_attributes = True


class ReadOpenUserInfo(BaseModel):
    id: int
    referrer_id: int | None = None
    is_email_verified: bool

    username: str | None = None
    telephone: str | None = None
    email: str | None = None

    firstname: str
    patronymic: str | None = None
    surname: str | None = None
    other_names: str | None = None
    gender: Gender
    date_of_birth: date | None = None

    confidentiality: int = DEFAULT_CONFIDENTIALITY
    is_staff: bool = False

    class Config:
        from_attributes = True


def get_open_user_info(user: User) -> dict:
    return user.convert_to(ReadOpenUserInfo).model_dump(exclude=user.get_private_field_names())
