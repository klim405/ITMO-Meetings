class APIError(Exception):
    """ Ошибка при доступе к api ресурсу. """
    http_code = 500
    message = ''

    def __init__(self, data=None):
        super().__init__(self.message)
        self.data = data

    def get_data(self):
        return {} if self.data is None else self.data

    @property
    def status_code(self):
        return self.http_code


class BadRequestAPIError(APIError):
    """ Противоречащий запрос (http 400) """
    http_code = 400
    message = 'Противоречащий запрос'

    def get_data(self):
        return {'errors': self.data}


class ValidationAPIError(APIError):
    """ Валидационная ошибка (http 400) """
    http_code = 400
    message = 'Ошибка при валидации'

    def get_data(self):
        return {'validation_errors': self.data}


class ObjectNotFoundAPIError(APIError):
    """ Объект не найден (http 404) """
    http_code = 404
    message = 'Объект не найден'


class PermissionAPIError(APIError):
    """ Отказано в доступе (http 403) """
    http_code = 403
    message = 'Отказано в доступе'


class UnauthorizedAPIError(APIError):
    """ Ошибка аутентификации (http 401) """
    http_code = 401
    message = 'Ошибка авторизации'

    def get_data(self):
        return {'errors': self.data}


