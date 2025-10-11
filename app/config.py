import os
from pathlib import Path

# БД по умолчанию — внутри репозитория, но в игнорируемой папке
DEFAULT_DB_PATH = Path("app/data/data.db")
# Позволяем переопределить через переменную окружения DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")
