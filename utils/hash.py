import hashlib


def make_hash(content) -> str:
    return hashlib.md5(content.encode("utf-8")).hexdigest()
