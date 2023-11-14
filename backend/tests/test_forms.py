import re
import unittest

from app.forms.exceptions import ValidationError
from app.forms.validators import MaxLengthValidator, NotNullValidator, RegexValidator, NotEmptyValidator, \
    MinLengthValidator, LengthValidator, EmailValidator, PasswordValidator, MaxValueValidator, MinValueValidator, \
    ValueInRangeValidator


class TestValidators(unittest.TestCase):
    def setUp(self) -> None:
        self.validator_msg = 'test_message'

    def check_validation_error_msg(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.fail('Не вызвано исключение ValidationError')
        except ValidationError as e:
            self.assertEqual(e.validation_error, self.validator_msg, 'Неверно установленно сообщение об ошибки')

    def test_max_length_validator(self):
        validator = MaxLengthValidator(10, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, '1'*11)
        self.assertRaises(ValidationError, validator.validate, '1'*20)
        self.check_validation_error_msg(validator.validate, '1'*11)
        self.assertTrue(validator.validate(''))
        self.assertTrue(validator.validate(None))
        self.assertTrue(validator.validate('='*10))
        self.assertTrue(validator.validate('1234'))

    def test_min_length_validator(self):
        validator = MinLengthValidator(10, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, '1'*8)
        self.assertRaises(ValidationError, validator.validate, '')
        self.check_validation_error_msg(validator.validate, '1')
        self.assertTrue(validator.validate(None))
        self.assertTrue(validator.validate('='*10))
        self.assertTrue(validator.validate('='*20))

    def test_length_validator(self):
        validator = LengthValidator(5, 10, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, '1'*12)
        self.assertRaises(ValidationError, validator.validate, '1'*4)
        self.assertRaises(ValidationError, validator.validate, '')
        self.check_validation_error_msg(validator.validate, '12')
        self.assertTrue(validator.validate(None))
        self.assertTrue(validator.validate('='*10))
        self.assertTrue(validator.validate('='*5))
        self.assertTrue(validator.validate('='*7))

    def test_not_null_validator(self):
        validator = NotNullValidator(msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, None)
        self.check_validation_error_msg(validator.validate, None)
        self.assertTrue(validator.validate(""))
        self.assertTrue(validator.validate(0))
        self.assertTrue(validator.validate(123))
        self.assertTrue(validator.validate('1234'))

    def test_regex_validator(self):
        validator = RegexValidator(r'\d{3}[a-z]', flags=re.IGNORECASE, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, 'None')
        self.assertRaises(ValidationError, validator.validate, '12342332332A')
        self.assertRaises(ValidationError, validator.validate, '')
        self.check_validation_error_msg(validator.validate, '')
        self.assertTrue(validator.validate("333A"))
        self.assertTrue(validator.validate('123a'))
        self.assertTrue(validator.validate(None))

    def test_not_empty_validator(self):
        validator = NotEmptyValidator(msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, '')
        self.check_validation_error_msg(validator.validate, '')
        self.assertTrue(validator.validate("333A"))
        self.assertTrue(validator.validate(None))

    def test_email_validator(self):
        validator = EmailValidator(msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, '121231@nfje4r432')
        self.assertRaises(ValidationError, validator.validate, '121231nfje4r432')
        self.assertRaises(ValidationError, validator.validate, '121231@nfje4r432.1332g34t')
        self.assertRaises(ValidationError, validator.validate, '121231@nfje4r.432')
        self.assertRaises(ValidationError, validator.validate, '')
        self.check_validation_error_msg(validator.validate, '')
        self.assertTrue(validator.validate("121231@nfje4r432.co"))
        self.assertTrue(validator.validate("121231@nfje4r432.commmm"))
        self.assertTrue(validator.validate(None))

        validator2 = EmailValidator('gmail.com', 'mail.ru', msg=self.validator_msg)
        self.assertRaises(ValidationError, validator2.validate, '121231@fire.fox')
        self.assertTrue(validator2.validate("121+231@gmail.com"))
        self.assertTrue(validator2.validate("121ghgh231@mail.ru"))

    def test_password_validator(self):
        validator = PasswordValidator(ignore_case=True, use_special_symbols=False, msg=self.validator_msg)
        validator2 = PasswordValidator(ignore_case=True, use_special_symbols=True, msg=self.validator_msg)
        validator3 = PasswordValidator(ignore_case=False, use_special_symbols=False, msg=self.validator_msg)
        validator4 = PasswordValidator(ignore_case=False, use_special_symbols=True, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, '123fff')
        self.assertRaises(ValidationError, validator.validate, '12345678')
        self.assertRaises(ValidationError, validator.validate, 'abcdefgh')

        # validator 2
        self.assertRaises(ValidationError, validator2.validate, 'ab123cdefgh')

        # validator 3
        self.assertRaises(ValidationError, validator3.validate, '121231nfje4r432')
        self.assertRaises(ValidationError, validator3.validate, '1245###234ghh')

        # validator 4
        self.assertRaises(ValidationError, validator4.validate, '124FF345fffadd')
        self.assertRaises(ValidationError, validator.validate, '')
        self.check_validation_error_msg(validator.validate, '')

        self.assertTrue(validator.validate('123456ucer8997'))
        self.assertTrue(validator.validate('123456uc'))
        self.assertTrue(validator.validate('1234#56uc'))
        self.assertTrue(validator.validate('ucccc444456'))
        self.assertTrue(validator2.validate('12#456uc'))
        self.assertTrue(validator3.validate("1234#Ff34fgh"))
        self.assertTrue(validator3.validate("f2Ff34fgh"))
        self.assertTrue(validator4.validate("1234#Ff34fgh"))
        self.assertTrue(validator.validate(None))

    def test_value_validator(self):
        validator = ValueInRangeValidator(-100, 100, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, -101)
        self.assertRaises(ValidationError, validator.validate, 101)
        self.assertRaises(ValidationError, validator.validate, 100.50)
        self.check_validation_error_msg(validator.validate, -1000)
        self.assertTrue(validator.validate(100))
        self.assertTrue(validator.validate(-100))
        self.assertTrue(validator.validate(0))
        self.assertTrue(validator.validate(99.9))
        self.assertTrue(validator.validate(None))

    def test_max_value_validator(self):
        validator = MaxValueValidator(100, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, 101)
        self.assertRaises(ValidationError, validator.validate, 1000)
        self.assertRaises(ValidationError, validator.validate, 1000.00)
        self.check_validation_error_msg(validator.validate, 1000)
        self.assertTrue(validator.validate(0))
        self.assertTrue(validator.validate(-111))
        self.assertTrue(validator.validate(-99))
        self.assertTrue(validator.validate(-100))
        self.assertTrue(validator.validate(None))

    def test_min_value_validator(self):
        validator = MinValueValidator(100, msg=self.validator_msg)
        self.assertRaises(ValidationError, validator.validate, 99)
        self.assertRaises(ValidationError, validator.validate, 0)
        self.assertRaises(ValidationError, validator.validate, 99.99)
        self.check_validation_error_msg(validator.validate, -1000)
        self.assertTrue(validator.validate(100))
        self.assertTrue(validator.validate(101))
        self.assertTrue(validator.validate(10000))
        self.assertTrue(validator.validate(None))
