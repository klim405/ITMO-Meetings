from datetime import date

from pydantic import BaseModel, Field, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

from app.models.user import Gender, DEFAULT_CONFIDENTIALITY


class UserPhoneNumber(PhoneNumber):
    phone_format: str = 'INTERNATIONAL'


class UserBase(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=20, pattern=r'^\w+$', examples=['elison98'])
    telephone: UserPhoneNumber = Field(examples=['+79001234567'])
    email: EmailStr = Field(max_length=320, examples=['elison@example.com'])

    firstname: str = Field(max_length=20, pattern=r'^[А-ЯA-Z][а-яa-z]+$', examples=['Elison'])
    patronymic: str | None = Field(default=None, max_length=20, pattern=r'^[А-ЯA-Z][а-яa-z]+$', examples=[None])
    surname: str = Field(max_length=20, pattern=r'^[А-ЯA-Z][а-яa-z]+$', examples=['Argent'])
    other_names: str | None = Field(default=None, max_length=256, pattern=r'^[А-Яа-яA-Za-z\s]+$', examples=[None])
    gender: Gender
    date_of_birth: date


class CreateUser(UserBase):
    password: str = Field(min_length=8, max_length=30)


class UpdateUser(UserBase):
    pass


class ChangeUserPassword(BaseModel):
    password: str = Field(min_length=8, max_length=30)


class ReadUser(UserBase):
    id: int
    referrer_id: int | None = None
    confidentiality: int = DEFAULT_CONFIDENTIALITY
    is_staff: bool = False

    class Config:
        from_attributes = True
