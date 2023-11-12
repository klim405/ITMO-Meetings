import json

from flask import abort

from app import db
from app.models.exceptions import DBAttributeError


class DBModelMixin:
    @classmethod
    def get(cls, *pk):
        return db.session.get(cls, pk)

    @classmethod
    def get_or_404(cls, *pk):
        obj = cls.get(*pk)
        if obj is None:
            raise abort(404)
        return obj

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class DBModelAPIMixin:
    model_json_attrs = None

    def from_json(self, json_data):
        self.from_dict(json.loads(json_data))

    @classmethod
    def _parse_model(cls):
        cls.model_json_attrs = []
        for attr_name in dir(cls):
            attr_obj = getattr(cls, attr_name)
            if attr_obj.__class__.__name__ == 'InstrumentedAttribute' \
                    and attr_obj.impl.__class__.__name__ == 'ScalarAttributeImpl':
                cls.model_json_attrs.append(
                    (attr_name, attr_obj.type.python_type)
                )
            elif attr_obj.__class__.__name__ == 'property':
                try:
                    cls.model_json_attrs.append(
                        (attr_name, getattr(cls, attr_name + '_from_json'))
                    )
                except AttributeError:
                    msg = f'Не найден метод-конвертор {attr_name}_from_json в классе модели {cls.__name__}.'
                    raise DBAttributeError(msg)

    def from_dict(self, data):
        if self.model_json_attrs is None:
            self._parse_model()
        for attr_name, attr_type in self.model_json_attrs:
            try:
                setattr(self, attr_name, attr_type(data[attr_name]))
            except KeyError:
                pass

    def to_json(self) -> dict:
        return {}