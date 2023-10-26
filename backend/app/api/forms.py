from app.forms.forms import ModelFormAPI
from app.forms.validators import NotNullValidator
from app.models.models import User


class UserForm(ModelFormAPI):
    class Meta:
        model = User
        excluded = ['password_hash']

    @staticmethod
    def get_password_type():
        return str

    @staticmethod
    def get_password_validators():
        return [NotNullValidator()]
