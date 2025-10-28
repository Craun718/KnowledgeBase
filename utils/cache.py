from diskcache import Cache
from pathlib import Path

pwd = Path.cwd()

cache = Cache(pwd / "tmp/cache")
