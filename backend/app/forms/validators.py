import re

from abc import ABC, abstractmethod

from app.forms.exceptions import ValidationError


class Validator(ABC):
    @abstractmethod
    def validate(self, value) -> bool:
        pass

    def __repr__(self):
        return self.__class__.__name__


class ValueInRangeValidator(Validator):
    def __init__(self, minimum, maximum, msg='value_out_of_range'):
        if minimum >= maximum:
            raise ValueError('The max value must be better than the min value')
        self.mn = minimum
        self.mx = maximum
        self.msg = msg

    def validate(self, value) -> bool:
        if value is not None and not (self.mn <= value <= self.mx):
            raise ValidationError(self.msg)
        return True


class MaxValueValidator(Validator):
    def __init__(self, maximum, msg='max_value'):
        self.mx = maximum
        self.msg = msg

    def validate(self, value) -> bool:
        if value is not None and self.mx < value:
            raise ValidationError(self.msg)
        return True


class MinValueValidator(Validator):
    def __init__(self, minimum, msg='min_value'):
        self.mn = minimum
        self.msg = msg

    def validate(self, value) -> bool:
        if value is not None and value < self.mn:
            raise ValidationError(self.msg)
        return True


class LengthValidator(Validator):
    def __init__(self, min_length, max_length, msg='wrong_length'):
        self.msg = msg
        if min_length >= max_length:
            raise ValueError('The max length must be better than the min length')
        self.max_length = max_length
        self.min_length = min_length

    def validate(self, value) -> bool:
        if value is not None and (self.min_length > len(value) or len(value) > self.max_length):
            raise ValidationError(self.msg)
        return True

    def __repr__(self):
        return f'{self.__class__.__name__}({self.min_length}, {self.max_length})'


class MaxLengthValidator(Validator):
    def __init__(self, max_length, msg='max_length'):
        self.msg = msg
        self.max_length = max_length
    
    def validate(self, value) -> bool:
        if value is not None and len(value) > self.max_length:
            raise ValidationError(self.msg)
        return True

    def __repr__(self):
        return f'{self.__class__.__name__}({self.max_length})'


class MinLengthValidator(Validator):
    def __init__(self, min_length, msg='min_length'):
        self.msg = msg
        self.min_length = min_length

    def validate(self, value) -> bool:
        if value is not None and len(value) < self.min_length:
            raise ValidationError(self.msg)
        return True

    def __repr__(self):
        return f'{self.__class__.__name__}({self.min_length})'


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
        if value is not None and len(value) == 0:
            raise ValidationError(self.msg)
        return True


class RegexValidator(Validator):
    def __init__(self, pattern, flags=0, msg='regex'):
        self.msg = msg
        self.pattern = pattern
        self.flags = flags

    def validate(self, value) -> bool:
        if value is not None and re.fullmatch(self.pattern, value, self.flags) is None:
            raise ValidationError(self.msg)
        return True


class PasswordValidator(Validator):
    def __init__(self, min_length=8, ignore_case=False, use_special_symbols=False, msg='simple_password'):
        if ignore_case and not use_special_symbols:
            self.pattern = re.compile(
                r"^(?=.*[A-Za-z])(?=.*\d)"
                r"[a-zA-Z\d+=\-~!@#$%^&*(){}\[\];:,.`'\"\\/|]{" + str(min_length) + ",}$")
        elif ignore_case and use_special_symbols:
            self.pattern = re.compile(
                r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[+=\-~!@#$%^&*(){}\[\];:,.`'\"\\/|])"
                r"[a-zA-Z\d+=\-~!@#$%^&*(){}\[\];:,.`'\"\\/|]{" + str(min_length) + ",}$")
        elif not ignore_case and not use_special_symbols:
            self.pattern = re.compile(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)"
                r"[a-zA-Z\d+=\-~!@#$%^&*(){}\[\];:,.`'\"\\/|]{" + str(min_length) + ",}$")
        elif not ignore_case and use_special_symbols:
            self.pattern = re.compile(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[+=\-~!@#$%^&*(){}\[\];:,.`'\"\\/|])"
                r"[a-zA-Z\d+=\-~!@#$%^&*(){}\[\];:,.`'\"\\/|]{" + str(min_length) + ",}$")

        self.msg = msg

    def validate(self, value) -> bool:
        if value is None:
            return True
        if self.pattern.match(value) is None:
            raise ValidationError(self.msg)
        return True


class EmailValidator(Validator):
    PATTERN = re.compile(r"\A[A-Z0-9+_.-]+@([A-Z0-9.-]+\.[A-Z]{2,6})\Z", flags=re.IGNORECASE)

    def __init__(self, *domains, msg='wrong_email'):
        self.domains = domains
        self.msg = msg

    def validate(self, value) -> bool:
        if value is None:
            return True
        match = self.PATTERN.match(value)
        if match is None:
            raise ValidationError(self.msg)
        if self.domains and match.group(1) not in self.domains:
            raise ValidationError(self.msg)
        return True
