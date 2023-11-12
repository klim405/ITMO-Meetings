import re
from datetime import datetime, timedelta, timezone
import enum
import uuid

from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.forms.validators import RegexValidator, MinValueValidator, EmailValidator, MaxValueValidator
from app.models.exceptions import AuthTokenError, ModelError
from app.models.mixins import DBModelMixin, DBModelAPIMixin


class AuthToken(DBModelMixin, DBModelAPIMixin, db.Model):
    __tablename__ = 'auth_token'
    access_token = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    refresh_token = db.Column(db.Uuid, nullable=False, unique=True, default=uuid.uuid4)
    expire_time = db.Column(db.DateTime(timezone=True), nullable=False,
                            default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5))
    is_refresh_available = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('person.user_id'))

    def is_active(self):
        return self.expire_time > datetime.now(timezone.utc) and self.is_refresh_available

    def refresh(self):
        if not self.is_refresh_available:
            raise AuthTokenError('Токен уже был обновлен либо деактивирован.')
        new_token = AuthToken()
        new_token.user_id = self.user_id
        self.deactivate()
        db.session.add(self)
        db.session.add(new_token)
        db.session.commit()
        return new_token

    def deactivate(self):
        self.is_refresh_available = False

    def to_json(self):
        json_dict = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expire_in': 300,
            'token_type': 'bearer'
        }
        return json_dict


favorite_category = db.Table(
    'favorite_category',
    db.Column('user_id', db.Integer, db.ForeignKey('person.user_id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.category_id'), primary_key=True)
)


class Sex(enum.Enum):
    male = 'male'
    female = 'female'


class Confidentiality:
    SHOW_AVATAR     = 0b100000000
    SHOW_USERNAME   = 0b010000000
    SHOW_PATRONYMIC = 0b001000000
    SHOW_SURNAME    = 0b000100000
    SHOW_AGE        = 0b000010000
    SHOW_TELEPHONE  = 0b000001000
    SHOW_EMAIL      = 0b000000100
    SHOW_CHANNELS   = 0b000000010
    SHOW_CATEGORIES = 0b000000001


ALL_CONFIDENTIALITY = 0b111111111
DEFAULT_CONFIDENTIALITY = Confidentiality.SHOW_AVATAR | Confidentiality.SHOW_USERNAME | \
                          Confidentiality.SHOW_SURNAME | Confidentiality.SHOW_CHANNELS


class User(DBModelMixin, db.Model):
    __tablename__ = 'person'
    id = db.Column('user_id', db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('person.user_id'))
    referrer = db.relationship('User', remote_side=[id])
    username = db.Column(db.String(20), unique=True, nullable=True,
                         info={'validators': [RegexValidator(r'\w{3,20}')]})
    firstname = db.Column(db.String(20), nullable=False,
                          info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-]{1,20}')]})
    patronymic = db.Column(db.String(20), nullable=True,
                           info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-]{3,20}')]})
    surname = db.Column(db.String(20), nullable=False,
                        info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-]{3,20}')]})
    other_names = db.Column(db.String(256), nullable=True,
                            info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-\s]{3,256}')]})
    sex = db.Column(db.Enum(Sex), nullable=False)
    age = db.Column(db.Integer, nullable=False,
                    info={'validators': [MinValueValidator(0)]})
    telephone = db.Column(db.String(16), nullable=False, unique=True,
                          info={'validators': [RegexValidator(r'\+[\d]{11,15}')]})
    email = db.Column(db.String(320), nullable=False, unique=True,
                      info={'validators': [EmailValidator()]})
    password_hash = db.Column(db.String(182), nullable=False)
    confidentiality = db.Column(db.Integer, nullable=False, default=DEFAULT_CONFIDENTIALITY)
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    favorite_categories = db.relationship('Category', secondary=favorite_category, lazy='select', cascade="all,delete",
                                          backref=db.backref('users', lazy='subquery'))
    auth_tokens = db.relationship('AuthToken', lazy='select', cascade="all,delete",
                                  backref=db.backref('user', lazy='subquery'))
    channel_members = db.relationship('ChannelMember', lazy='select', cascade="all,delete",
                                      backref=db.backref('user', lazy='subquery'))
    feedbacks = db.relationship('Feedback', lazy='select', cascade="all,delete",
                                backref=db.backref('user', lazy='subquery'))

    def __init__(self, *args, **kwargs):
        pwd = kwargs.pop('password') if 'password' in kwargs else None
        super(User, self).__init__(*args, **kwargs)
        if pwd is not None:
            self.password = pwd

    @classmethod
    def get_by_login(cls, login):
        """ Возвращает объект модели по одному из параметров: email, username, telephone, иначе None. """
        user = cls.query.filter_by(email=login).first()
        if user is None:
            user = cls.query.filter_by(username=login).first()
        if user is None:
            user = cls.query.filter_by(telephone=login).first()
        return user

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """ Хэширует и устанавливает пароль. """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha512', salt_length=32)

    def verify_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

    def gen_auth_token(self) -> AuthToken:
        token = AuthToken()
        token.user_id = self.id
        token.save()
        return token

    def deactivate_all_auth_tokens(self):
        for token in self.auth_tokens:
            token.deactivate()
            db.session.add(token)
        db.session.commit()

    def deactivate_and_save(self):
        self.deactivate_all_auth_tokens()
        self.is_active = False
        self.save()

    def to_json(self) -> dict:
        json_dict = {
            'id': self.id,
            'firstname': self.firstname,
            'sex': self.sex.value,
            'confidentiality': self.confidentiality,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
        }
        return json_dict


class Category(DBModelMixin, db.Model):
    __tablename__ = 'category'
    id = db.Column('category_id', db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)

    def to_json(self):
        json_dict = {
            'id': self.id,
            'title': self.title
        }
        return json_dict


class Channel(DBModelMixin, DBModelAPIMixin, db.Model):
    __tablename__ = 'channel'
    id = db.Column('channel_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    members_cnt = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=True)
    is_personal = db.Column(db.Boolean, nullable=False, default=False)
    is_require_confirmation = db.Column(db.Boolean, nullable=False, default=False)
    channel_members = db.relationship('ChannelMember', lazy='dynamic', cascade="all,delete",
                                      backref=db.backref('channel', lazy='subquery'))

    def get_guest_permissions(self):
        """ Возвращает права доступные гостю канала. """
        if self.is_require_confirmation:
            return Permission.NONE
        return Permission.SEE_MEETING | Permission.SEE_MEMBERS

    def add_member(self, user: User, permissions=None):
        if user.id is None:
            raise ModelError('User must have id')
        if self.id is None:
            raise ModelError('Channel must have id')
        if ChannelMember.query.filter_by(user_id=user.id, channel_id=self.id).first():
            raise ModelError(f'User(id={user.id}) already is member of channel(id={self.id})')
        channel_member = ChannelMember(user_id=user.id, channel_id=self.id, permissions=permissions)
        channel_member.save()

    def to_json(self):
        json_dict = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rating': self.rating,
            'is_personal': self.is_personal,
            'is_require_confirmation': self.is_require_confirmation,
        }
        return json_dict


class Permission:
    """ Права ChannelMember на внесение изменений в канале """
    IS_OWNER         = 0b10000000
    DELETE_CHANNEL   = 0b01000000
    UPDATE_CHANNEL   = 0b00100000
    GIVE_ACCESS      = 0b00010000
    UPDATE_MEETING   = 0b00001000
    SEE_MEMBERS      = 0b00000100
    SEE_MEETING      = 0b00000010
    JOIN_TO_MEETING  = 0b00000001
    NONE             = 0b00000000


class Role:
    """ Роли подписчиков канала """
    OWNER = Permission.IS_OWNER | Permission.UPDATE_CHANNEL | Permission.DELETE_CHANNEL \
        | Permission.GIVE_ACCESS | Permission.UPDATE_MEETING | Permission.SEE_MEMBERS \
        | Permission.SEE_MEETING | Permission.JOIN_TO_MEETING
    ADMIN = Permission.UPDATE_CHANNEL | Permission.GIVE_ACCESS | Permission.UPDATE_MEETING \
        | Permission.SEE_MEMBERS | Permission.SEE_MEETING | Permission.JOIN_TO_MEETING
    EDITOR = Permission.UPDATE_MEETING | Permission.SEE_MEMBERS | Permission.SEE_MEETING \
        | Permission.JOIN_TO_MEETING
    MEMBER = Permission.SEE_MEMBERS | Permission.SEE_MEETING | Permission.JOIN_TO_MEETING
    SUBSCRIBER = Permission.NONE
    BLOCKED = Permission.SEE_MEMBERS | Permission.SEE_MEETING

    @classmethod
    def to_json(cls):
        json_dict = {
            'OWNER': cls.OWNER,
            'ADMIN': cls.ADMIN,
            'EDITOR': cls.EDITOR,
            'MEMBER': cls.MEMBER,
            'SUBSCRIBER': cls.SUBSCRIBER,
            'BLOCKED': cls.BLOCKED
        }
        return json_dict


class ChannelMember(DBModelMixin, db.Model):
    __tablename__ = 'channel_member'
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['channel_id', 'user_id'],
            ['channel_member.channel_id', 'channel_member.user_id']
        ),
    )
    channel_id = db.Column('channel_id', db.Integer, db.ForeignKey('channel.channel_id'), primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('person.user_id'), primary_key=True)

    date_of_join = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    permissions = db.Column(db.Integer, nullable=False, default=Permission.NONE)
    notify_about_meeting = db.Column(db.Boolean, nullable=False, default=False)

    @classmethod
    def get(cls, user, channel):
        user_id = user.id if isinstance(user, User) else int(user)
        channel_id = channel.id if isinstance(channel, Channel) else int(channel)
        return cls.query.filter_by(user_id=user_id, channel_id=channel_id).first()

    def has_permission(self, permission):
        """ Проверяет есть ли требуемое право в списке прав. """
        return self.permissions & permission == permission

    @classmethod
    def get_by_role(cls, channel, role: int):
        return cls.query.filter_by(channel_id=channel.id, permissions=role)

    def to_json(self):
        json_dict = {
            'channel_id': self.channel_id,
            'user_id': self.user_id,
            'date_of_join': self.date_of_join,
            'permissions': self.permissions,
            'notify_about_meeting': self.notify_about_meeting,
        }
        return json_dict


meeting_category = db.Table(
    'meeting_category',
    db.Column('meeting_id', db.Integer, db.ForeignKey('meeting.meeting_id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.category_id'), primary_key=True)
)

meeting_member = db.Table(
    'meeting_member',
    db.Column('meeting_id', db.Integer, db.ForeignKey('meeting.meeting_id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('person.user_id'), primary_key=True)
)


class Meeting(DBModelMixin, DBModelAPIMixin, db.Model):
    __tablename__ = 'meeting'
    id = db.Column('meeting_id', db.Integer, primary_key=True)
    channel_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'channel.channel_id',
            ondelete='CASCADE',
            onupdate='CASCADE'
        ),
        nullable=False,
    )
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime(timezone=True),
                               db.CheckConstraint('start_datetime > CURRENT_TIMESTAMP'),
                               nullable=False)
    duration = db.Column(db.Interval)
    address = db.Column(db.String(512), nullable=False)
    capacity = db.Column(
        db.Integer,
        db.CheckConstraint('capacity > 0'),
        default=4,
        info={'validators': MinValueValidator(1)}
    )
    price = db.Column(
        db.Integer,
        db.CheckConstraint('price >= 0'),
        default=0,
        info={'validators': MinValueValidator(0)}
    )
    minimum_age = db.Column(
        db.Integer,
        db.CheckConstraint('minimum_age >= 0'),
        default=0,
        info={'validators': MinValueValidator(0)}
    )
    maximum_age = db.Column(
        db.Integer,
        db.CheckConstraint('maximum_age >= 0'),
        default=150,
        info={'validators': MinValueValidator(0)}
    )
    only_for_itmo_students = db.Column(db.Boolean, nullable=False, default=False)
    only_for_russians = db.Column(db.Boolean, nullable=False, default=False)
    rating = db.Column(db.Float, default=None)

    members = db.relationship('User', secondary=meeting_member, lazy='subquery',
                              backref=db.backref('meetings', lazy=True))
    categories = db.relationship('Category', secondary=meeting_category, lazy='subquery',
                                 backref=db.backref('meetings', lazy=True))
    feedbacks = db.relationship('Feedback', lazy='select', cascade="all,delete",
                                backref=db.backref('meeting', lazy='subquery'))

    def to_json(self) -> dict:
        json_dict = {
            'channel_id': self.channel_id,
            'title': self.title,
            'description': self.description,
            'start_datetime': self.start_datetime,
            'duration': self.duration,
            'address': self.address,
            'capacity': self.capacity,
            'price': self.price,
            'minimum_age': self.minimum_age,
            'maximum_age': self.maximum_age,
            'only_for_itmo_students': self.maximum_age,
            'only_for_russians': self.only_for_russians,
            'rating': round(self.rating, 2),
            'categories': [c.to_json() for c in self.categories]
        }
        return json_dict


class Feedback(DBModelMixin, db.Model):
    __tablename__ = 'feedback'
    __table_args__ = (
        db.UniqueConstraint('meeting_id', 'user_id', name='meeting_member_pk'),
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('person.user_id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey('meeting.meeting_id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
    rate = db.Column(
        db.Integer,
        db.CheckConstraint('rate >= 0 and rate <= 5',
                           info={'validators': [MinValueValidator(0), MaxValueValidator(5)]}),
        nullable=False
    )
