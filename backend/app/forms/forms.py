import json
from typing import List

from app.forms.exceptions import ValidationError, ModelFormError
from app.forms.validators import NotNullValidator, MaxLengthValidator


class FormField:
    """ Класс описывает поле формы и содержит валидаторы. """

    def __init__(self, attr_name, model_field):
        self.name = attr_name
        self.model_field = model_field

        self._default = None
        if model_field.default is not None:
            self._default = model_field.default.arg

        self.validators = []
        if self.model_field.info is not None:
            self.validators = self.model_field.info.get('validators', []).copy()

        self.is_unique = bool(model_field.unique)

        if not model_field.primary_key and model_field.nullable is False:
            self.validators.append(NotNullValidator())
        self.set_type_constrains()

    def set_type_constrains(self):
        if self.model_field.type.__class__ == 'String':
            self.validators.append(MaxLengthValidator(self.model_field.type.length))

    @property
    def default(self):
        if callable(self._default):
            return self._default()
        return self._default

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
        return f'<{self.name} {self.validators}>'


class PropertyField:
    def __init__(self, attr_name, python_type, validators=None, can_null=True, default=None):
        self.name = attr_name
        self.python_type = python_type
        self._default = default
        self.validators = list() if validators is None else validators
        self.is_unique = False
        if not can_null:
            self.validators.append(NotNullValidator())

    @property
    def default(self):
        if callable(self._default):
            return self._default()
        return self._default

    @default.setter
    def default(self, val):
        raise AttributeError('default is not writable attribute')

    def __repr__(self):
        return f'<{self.name} {self.validators}>'


class ModelFormAPI:
    """ Класс формы основанный на модели db.Model.
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
            try:
                self.form_data[field.name] = field.python_type(raw_value) if raw_value is not None else None
            except ValueError:
                self.form_data[field.name] = None
                self.validation_errors.setdefault(field.name, []).append('invalid_type')
            if field.name in self.pk_fields:
                pk[field.name] = self.form_data.get(field.name, None)

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
        """ Вызывает cls.get_{имя свойства}_type и возвращает тип указанного свойства. """
        try:
            return getattr(cls, f'get_{prop_name}_type')()
        except AttributeError:
            return None

    @classmethod
    def _get_prop_default(cls, prop_name):
        """ Вызывает cls.get_{имя свойства}_default и возвращает значение по умолчанию указанного свойства. """
        try:
            return getattr(cls, f'get_{prop_name}_default')()
        except AttributeError:
            return None

    @classmethod
    def _get_prop_validators(cls, prop_name):
        """ Вызывает cls.get_{имя свойства}_validators и возвращает валидаторы указанного свойства. """
        try:
            return getattr(cls, f'get_{prop_name}_validators')()
        except AttributeError:
            return []

    @classmethod
    def _init_meta(cls):
        """ Инициализирует переопределенный класс meta, добавляя неуказанные атрибуты. """
        attrs = list(filter(lambda x: x[0] != '_', dir(cls.Meta)))
        if 'fields' not in attrs:
            setattr(cls.Meta, 'fields', [])
        if 'excluded' not in attrs:
            setattr(cls.Meta, 'excluded', [])

    @classmethod
    def _init_form_fields(cls):
        """ Инициализирует массив полей формы используя рефлексию указанной модели (Meta.model). """
        cls._init_meta()
        if cls.form_fields is None:
            cls.form_fields = []
            cls.Meta.model()
            attrs = cls.Meta.fields if cls.Meta.fields else filter(lambda x: x[0] != '_', dir(cls.Meta.model))
            for attr_name in attrs:
                attr_obj = getattr(cls.Meta.model, attr_name)
                if cls._is_db_attr(attr_obj):
                    if attr_obj.primary_key:
                        cls.pk_fields.append(attr_name)
                    if attr_name in cls.Meta.excluded:
                        continue
                    cls._init_form_field(attr_name, attr_obj)

                elif cls._is_prop_attr(attr_name, attr_obj):
                    if attr_name in cls.Meta.excluded:
                        continue
                    cls._init_prop_field(attr_name)

    @staticmethod
    def _is_db_attr(attr_obj) -> bool:
        """ Проверка является ли полем модели значение атрибута класса модели. """
        return attr_obj.__class__.__name__ == 'InstrumentedAttribute' \
               and attr_obj.impl.__class__.__name__ == 'ScalarAttributeImpl'

    @classmethod
    def _init_form_field(cls, attr_name, attr_obj):
        """ Инициализирует поле формы и добавляет его в форму. """
        form_field = FormField(attr_name, attr_obj)
        cls.form_fields.append(form_field)

    @classmethod
    def _is_prop_attr(cls, attr_name, attr_obj):
        """ Проверяет являться ли атрибут модели свойством. """
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

    def _validate_unique(self, field) -> bool:
        if self.form_data[field.name] is None:
            return True

        obj = self.Meta.model.query.filter_by(**{field.name: self.form_data[field.name]}).first()
        is_valid = True
        if obj is not None:
            for pk_field_name in self.pk_fields:
                is_valid &= getattr(obj, pk_field_name) == getattr(self.model_obj, pk_field_name)
            if not is_valid:
                self.validation_errors.setdefault(field.name, []).append('not_unique')
        return is_valid

    def validate(self) -> bool:
        """ Производит валидацию данных и возвращает результат проверки,
            во время валидации формируется словарь с ошибками, который можно получить вызвав get_errors().
            :return: bool - данные корректны"""
        is_valid = not bool(self.validation_errors)
        for field in self.form_fields:
            if field.is_unique:
                is_valid &= self._validate_unique(field)
            for validator in field.validators:
                is_valid &= self._validate_field(field.name, validator)
        return is_valid

    def _validate_field(self, field_name, validator) -> bool:
        try:
            return validator.validate(self.form_data[field_name])
        except ValidationError as e:
            self.validation_errors.setdefault(field_name, []).append(e.validation_error)
            return False

    def _fill_object(self):
        for k, v in self.form_data.items():
            setattr(self.model_obj, k, v)

    def get_object(self):
        """ Возвращает экземпляр модели c заполненными полями
            :return: db.Model """
        self._fill_object()
        return self.model_obj

    def save(self):
        """ Сохраняет и возвращает экземпляр модели
            :return: db.Model """
        self._fill_object()
        self.model_obj.save()
        return self.model_obj

    def get_errors(self):
        return self.validation_errors

    def __repr__(self):
        return f'<ModelFormAPI({self.Meta.model.__name__})>'
