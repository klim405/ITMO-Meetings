from app.forms.forms import ModelFormAPI
from app.forms.validators import NotNullValidator, PasswordValidator
from app.models.models import User, Channel, Meeting


class UserPasswordFormMixin:
    @staticmethod
    def get_password_type():
        return str

    @staticmethod
    def get_password_validators():
        return [NotNullValidator(), PasswordValidator()]


class UpdateUserForm(ModelFormAPI):
    class Meta:
        model = User
        excluded = ['id', 'password_hash', 'is_staff', 'is_active', 'referrer_id']


class UpdateUserFormForStaff(ModelFormAPI):
    """ Форма для администраторов сайта, позволяющая менять почти все поля формы. """
    class Meta:
        model = User
        excluded = ['id', 'password_hash', 'referrer_id']


class RegistrationUserForm(UserPasswordFormMixin, ModelFormAPI):
    class Meta:
        model = User
        excluded = ['id', 'password_hash', 'is_staff', 'is_active', 'referrer_id']


class ChangePasswordForm(UserPasswordFormMixin, ModelFormAPI):
    class Meta:
        model = User
        fields = ['password']


class ChannelForm(ModelFormAPI):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'is_require_confirmation']


class MeetingForm(ModelFormAPI):
    class Meta:
        model = Meeting
        excluded = ['id']
