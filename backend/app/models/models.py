from datetime import datetime, timedelta, timezone
import enum
import uuid

from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.forms.validators import RegexValidator, MinValueValidator, EmailValidator
from app.models.exceptions import AuthTokenError
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


class User(DBModelMixin, db.Model):
    __tablename__ = 'person'
    id = db.Column('user_id', db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('person.user_id'))
    referrer = db.relationship('User', remote_side=[id])
    username = db.Column(db.String(20), unique=True, nullable=True,
                         info={'validators': [RegexValidator(r'\w{3,20}')]})
    first_name = db.Column(db.String(20), nullable=False,
                           info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-]{1,20}')]})
    patronymic = db.Column(db.String(20), nullable=True,
                           info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-]{3,20}')]})
    last_name = db.Column(db.String(20), nullable=False,
                          info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-]{3,20}')]})
    other_names = db.Column(db.String(256), nullable=True,
                            info={'validators': [RegexValidator(r'[А-Яа-яA-Za-z\-\s]{3,256}')]})
    sex = db.Column(db.Enum(Sex), nullable=False)
    age = db.Column(db.Integer, nullable=False,
                    info={'validators': [MinValueValidator(0)]})
    telephone = db.Column(db.String(16), nullable=False,
                          info={'validators': [RegexValidator(r'\+[\d]{11,15}')]})
    email = db.Column(db.String(320), nullable=False,
                      info={'validators': [EmailValidator()]})
    password_hash = db.Column(db.String(182), nullable=False)
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    favorite_categories = db.relationship('Category', secondary=favorite_category, lazy='subquery',
                                          backref=db.backref('users', lazy='subquery'))
    auth_tokens = db.relationship('AuthToken', lazy='select', cascade="all,delete",
                                  backref=db.backref('user', lazy='subquery'))
    chanel_members = db.relationship('ChanelMember', lazy='select', cascade="all,delete",
                                     backref=db.backref('chanel', lazy='subquery'))
    feedbacks = db.relationship('Feedback', lazy='select', cascade="all,delete",
                                backref=db.backref('user', lazy='subquery'))

    def __init__(self, *args, **kwargs):
        pwd = kwargs.pop('password') if 'password' in kwargs else None
        super(User, self).__init__(*args, **kwargs)
        if pwd is not None:
            self.password = pwd

    @classmethod
    def get_by_login(cls, login):
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

    def to_json(self) -> dict:
        json_dict = {
            'id': self.id,
            'referrer_id': self.referrer_id,
            'username': self.username,
            'first_name': self.first_name,
            'patronymic': self.patronymic,
            'last_name': self.last_name
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


class Chanel(DBModelMixin, db.Model):
    __tablename__ = 'chanel'
    id = db.Column('chanel_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    is_personal = db.Column(db.Boolean, nullable=False, default=True)
    is_require_confirmation = db.Column(db.Boolean, nullable=False, default=False)
    chanel_members = db.relationship('ChanelMember', lazy='select', cascade="all,delete",
                                     backref=db.backref('chanel', lazy='subquery'))

    def to_json(self):
        json_dict = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rating': self.rating,
            'is_personal': self.is_personal,
            'is_require_confirmation': self.is_require_confirmation,
            'members': [m.to_json() for m in self.members]
        }
        return json_dict


class Access(enum.Enum):
    OWNER = 'owner'
    ADMIN = 'admin'
    EDITOR = 'editor'
    MEMBER = 'member'
    BANNED = 'banned'


class ChanelMember(DBModelMixin, db.Model):
    __tablename__ = 'chanel_member'
    chanel_id = db.Column('chanel_id', db.Integer, db.ForeignKey('chanel.chanel_id'), primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('person.user_id'), primary_key=True)

    date_of_join = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    type_of_access = db.Column(db.Enum(Access), nullable=False, default=Access.MEMBER)
    notify_about_meeting = db.Column(db.Boolean, nullable=False, default=False)

    def to_json(self):
        json_dict = {
            'user_id': self.user_id,
            'date_of_join': self.date_of_join,
            'type_of_access': self.type_of_access,
            'notify_about_meeting': self.notify_about_meeting
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


class Meeting(DBModelMixin, db.Model):
    __tablename__ = 'meeting'
    id = db.Column('meeting_id', db.Integer, primary_key=True)
    chanel_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'chanel.chanel_id',
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
        default=4
    )
    price = db.Column(
        db.Integer,
        db.CheckConstraint('price >= 0'),
        default=0
    )
    minimum_age = db.Column(
        db.Integer,
        db.CheckConstraint('minimum_age >= 0'),
        default=0
    )
    maximum_age = db.Column(
        db.Integer,
        db.CheckConstraint('maximum_age >= 0'),
        default=150
    )
    only_for_itmo_students = db.Column(db.Boolean, nullable=False, default=False)
    only_for_russians = db.Column(db.Boolean, nullable=False, default=False)

    members = db.relationship('User', secondary=meeting_member, lazy='subquery',
                              backref=db.backref('meetings', lazy=True))
    categories = db.relationship('Category', secondary=meeting_category, lazy='subquery',
                                 backref=db.backref('meetings', lazy=True))
    feedbacks = db.relationship('Feedback', lazy='select', cascade="all,delete",
                                backref=db.backref('meeting', lazy='subquery'))


class Feedback(DBModelMixin, db.Model):
    __tablename__ = 'feedback'
    __table_args__ = (
        db.UniqueConstraint('meeting_id', 'user_id', name='meeting_member_pk'),
    )
    id = db.Column('feedback_id', db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('person.user_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )
    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey('meeting.meeting_id',  ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )
    rate = db.Column(
        db.Integer,
        db.CheckConstraint('rate >= 0 and rate <= 5'),
        nullable=False
    )
