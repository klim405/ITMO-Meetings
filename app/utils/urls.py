from app import settings
from app.utils.hash import create_simple_hash


def get_email_confirm_url(user_id: int, user_email: str) -> str:
    return "http://%s:%s/user/confirm-email/?u=%s&t=%s" % (
        settings.server.host,
        settings.server.port,
        user_id,
        create_simple_hash(str(user_id) + user_email),
    )
