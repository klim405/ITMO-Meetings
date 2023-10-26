import json
from typing import List

from app.forms.exceptions import ValidationError, ModelFormError


class FormField:
    def __init__(self, attr_name, model_field):
        self.name = attr_name
        self.model_field = model_field
        self.has_default = model_field.default is not None

    @property
    def is_unique(self):
        return self.model_field.unique

    @is_unique.setter
    def is_unique(self, val):
        raise AttributeError('is_unique is not writable attribute')

    @property
    def can_null(self):
        return self.model_field.nullable

    @can_null.setter
    def can_null(self, val):
        raise AttributeError('can_null is not writable attribute')

    @property
    def validators(self):
        if self.model_field.info is not None:
            return self.model_field.info.get('validators', [])
        return []

    @validators.setter
    def validators(self, val):
        raise AttributeError('validators is not writable attribute')

    @property
    def default(self):
        if self.has_default:
            if self.model_field.default.is_callable:
                return self.model_field.default.arg()
            else:
                return self.model_field.default.arg
        return None

    @default.setter
    def default(self, val):
        raise AttributeError('default is not writable attribute')

    @property
    def python_type(self):
        return self.model_field.type.python_type

    @python_type.setter
    def python_type(self, val):
        raise AttributeError('python_type is not writable attribute')

    def __repr__(self):
        return f'<FormField {self.name}>'


class PropertyField:
    def __init__(self, attr_name, python_type, validators=None, can_null=True, default=None):
        self.name = attr_name
        self.python_type = python_type
        self.can_null = can_null
        self.is_unique = False
        self.default_val = default
        if validators is None:
            validators = []
        self.validators = validators

    @property
    def default(self):
        if callable(self.default_val):
            return self.default_val()
        else:
            return None

    @default.setter
    def default(self, val):
        raise AttributeError('default is not writable attribute')


class ModelFormAPI:
    """ Класс формы основанный на моделе db.Model.
    Во внутреннем классе Meta необходимо указать класс модели в статическом свойстве model.
    При указании модели будут определены все скалярные поля модели.
    Исключенные поля модели в форме указываются в виде списка в атрибуте Meta.excluded
    Список полей модели в форме указываются в виде списка в атрибуте Meta.fields.
    Если в модели имеются ленивые свойства (@property),
    для них необходимо следующие создать методы в классе формы:
    get_{prop_name}_type() - обязательный метод, возвращает парсер из json типа в тип,
    совместимый с аргументом сеттера свойства;
    get_{prop_name}_default() - необязательный метод, возвращает значение по умолчанию;
    get_{prop_name}_validators() - необязательный метод, возвращает список валидаторов.
    """
    form_fields = None
    pk_fields: List[str] = []

    def __init__(self, json_data, model_obj=None):
        if self.form_fields is None:
            self._init_form_fields()
        self.validation_errors = {}

        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        pk = {}
        self.form_data = {}
        for field in self.form_fields:
            raw_value = json_data.get(field.name, field.default)
            self.form_data[field.name] = field.python_type(raw_value) if raw_value is not None else None
            if field.name in self.pk_fields:
                pk[field.name] = self.form_data[field.name]

        if model_obj is None:
            if 0 < len(pk) < len(self.pk_fields):
                msg = 'Не верный первичный ключ'
                raise ModelFormError(msg)
            elif len(pk) == 0:
                model_obj = self.Meta.model()
            else:
                model_obj = self.Meta.model.query.filter_by(**pk).first()
                if model_obj is None:
                    model_obj = self.Meta.model()
        self.model_obj = model_obj

    class Meta:
        model = None
        fields = []
        excluded = []

    @classmethod
    def _get_prop_type(cls, prop_name):
        try:
            return getattr(cls, f'get_{prop_name}_type')()
        except AttributeError:
            return None

    @classmethod
    def _get_prop_default(cls, prop_name):
        try:
            return getattr(cls, f'get_{prop_name}_default')()
        except AttributeError:
            return None

    @classmethod
    def _get_prop_validators(cls, prop_name):
        try:
            return getattr(cls, f'get_{prop_name}_validators')()
        except AttributeError:
            return []

    @classmethod
    def _init_meta(cls):
        attrs = list(filter(lambda x: x[0] != '_', dir(cls.Meta)))
        if 'fields' not in attrs:
            setattr(cls.Meta, 'fields', [])
        if 'excluded' not in attrs:
            setattr(cls.Meta, 'excluded', [])

    @classmethod
    def _init_form_fields(cls):
        cls._init_meta()
        if cls.form_fields is None:
            cls.form_fields = []

            attrs = cls.Meta.fields if cls.Meta.fields else filter(lambda x: x[0] != '_', dir(cls.Meta.model))
            for attr_name in attrs:
                if attr_name in cls.Meta.excluded:
                    continue
                cls.Meta.model()
                attr_obj = getattr(cls.Meta.model, attr_name)
                if cls._is_db_attr(attr_obj):
                    cls._init_db_field(attr_name, attr_obj)
                elif cls._is_prop_attr(attr_name, attr_obj):
                    cls._init_prop_field(attr_name)

    @staticmethod
    def _is_db_attr(attr_obj):
        return attr_obj.__class__.__name__ == 'InstrumentedAttribute' \
               and attr_obj.impl.__class__.__name__ == 'ScalarAttributeImpl'

    @classmethod
    def _init_db_field(cls, attr_name, attr_obj):
        form_field = FormField(attr_name, attr_obj)
        cls.form_fields.append(form_field)
        if attr_obj.primary_key:
            cls.pk_fields.append(attr_name)

    @classmethod
    def _is_prop_attr(cls, attr_name, attr_obj):
        return attr_obj.__class__.__name__ == 'property' and cls._get_prop_type(attr_name)

    @classmethod
    def _init_prop_field(cls, prop_name):
        cls.form_fields.append(
            PropertyField(
                prop_name,
                cls._get_prop_type(prop_name),
                cls._get_prop_validators(prop_name),
                cls._get_prop_default(prop_name)
            ))

    def validate(self) -> bool:
        is_valid = True
        for field in self.form_fields:
            self._check_null(field)
            for validator in field.validators:
                is_valid &= self.validate_field(field.name, validator)
        return is_valid

    def _check_null(self, field):
        if not field.can_null and self.form_data[field.name] is None:
            is_valid = False
            self.validation_errors.setdefault(field.name, []).append('not_null')

    def validate_field(self, field_name, validator) -> bool:
        try:
            return validator.validate(self.form_data[field_name])
        except ValidationError as e:
            self.validation_errors.setdefault(field_name, []).append(e.validation_error)
            return False

    def fill_object(self):
        for k, v in self.form_data.items():
            setattr(self.model_obj, k, v)

    def get_object(self):
        self.fill_object()
        return self.model_obj

    def save(self):
        self.fill_object()
        self.model_obj.save()
        return self.model_obj

    def get_errors(self):
        raise self.validation_errors
