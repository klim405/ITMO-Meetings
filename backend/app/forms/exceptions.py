class ValidationError(Exception):
    def __init__(self, validation_error, *args):
        super().__init__(*args)
        self.validation_error = validation_error


class ModelFormError(AttributeError):
    pass
