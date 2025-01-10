import hashlib

from app import settings


def create_simple_hash(value: str | int) -> str:
    data = (settings.utils.simple_hash_pepper + str(value)).encode()
    return hashlib.sha224(data).hexdigest()


def verify_simple_hash(value: str | int, hash_: str) -> bool:
    data = (settings.utils.simple_hash_pepper + str(value)).encode()
    return hashlib.sha224(data).hexdigest() == hash_
