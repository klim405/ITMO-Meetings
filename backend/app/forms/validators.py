import re

from abc import ABC, abstractmethod

from app.forms.exceptions import ValidationError


class Validator(ABC):
    @abstractmethod
    def validate(self, value) -> bool:
        pass


class MaxLengthValidator(Validator):
    def __init__(self, max_length, msg='max_length'):
        self.msg = msg
        self.max_length = max_length
    
    def validate(self, value) -> bool:
        if value is not None and len(value) > self.max_length:
            raise ValidationError(self.msg)
        return True


class NotNullValidator(Validator):
    def __init__(self, msg='not_null'):
        self.msg = msg

    def validate(self, value) -> bool:
        if value is None:
            raise ValidationError(self.msg)
        return True


class NotEmptyValidator(Validator):
    def __init__(self, msg='is_empty'):
        self.msg = msg

    def validate(self, value) -> bool:
        if len(value) == 0:
            raise ValidationError(self.msg)
        return True


class RegexValidator(Validator):
    def __init__(self, pattern, flags, msg='regex'):
        self.msg = msg
        self.pattern = pattern
        self.flags = flags

    # todo: check func
    def validate(self, value) -> bool:
        if not re.fullmatch(self.pattern, value, self.flags):
            raise ValidationError(self.msg)
        return True
    

# todo: PasswordValidator
# class PasswordValidator(Validator):
#     pass


# todo: EmailValidator
# class EmailValidator(Validator):
#     pass
