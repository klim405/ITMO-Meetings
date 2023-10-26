from app.forms.forms import ModelFormAPI
from app.forms.validators import NotNullValidator, PasswordValidator
from app.models.models import User


class UserPasswordFormMixin:
    @staticmethod
    def get_password_type():
        return str

    @staticmethod
    def get_password_validators():
        return [NotNullValidator(), PasswordValidator()]


class UserForm(UserPasswordFormMixin, ModelFormAPI):
    class Meta:
        model = User
        excluded = ['password_hash', 'is_staff', 'is_active', 'referrer_id']


class ChangePasswordForm(UserPasswordFormMixin, ModelFormAPI):
    class Meta:
        model = User
        fields = ['id', 'password']
