class APIError(Exception):
    http_code = 500
    message = ''

    def __init__(self, *args, data=None):
        super().__init__(self.message)
        self.data = data

    def get_data(self):
        return self.data

    @property
    def status_code(self):
        return self.http_code


class ValidationAPIError(APIError):
    http_code = 400
    message = 'Ошибка при валидации'

    def get_data(self):
        return {'validation_errors': self.data}


class UnauthorizedAPIError(APIError):
    http_code = 401
    message = 'Ошибка авторизации'

    def get_data(self):
        return {'errors': self.data}


