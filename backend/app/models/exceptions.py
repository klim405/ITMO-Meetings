class AuthTokenError(Exception):
    pass


class ModelError(Exception):
    pass


class DBMixinError(Exception):
    pass


class DBAttributeError(DBMixinError):
    pass
