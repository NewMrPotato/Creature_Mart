import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
MINIMUM_AMOUNT = 52


@dataclass(frozen=True)
class Settings:
    token: str
    admin_ids: tuple[int, ...]
    tutor_ids: tuple[int, ...]
    tutor_links: tuple[str, ...]
    agreement_url: str
    support_url: str
    database_path: Path


def load_settings(base_dir: Path = BASE_DIR) -> Settings:
    values = {}
    env_file = base_dir / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, separator, value = line.partition("=")
                if not separator:
                    raise ValueError("Некорректная строка в .env")
                values[key.strip()] = value.strip().strip("\"'")
    legacy = base_dir / "data/text/config.txt"
    lines = []
    if legacy.exists():
        lines = [
            line.split("\\", 1)[0].strip()
            for line in legacy.read_text(encoding="utf-8-sig").splitlines()
        ]

    def get(key, index=None, default=""):
        fallback = lines[index] if index is not None and index < len(lines) else default
        return os.environ.get(key, values.get(key, fallback)).strip()

    def ids(key, index):
        try:
            result = tuple(
                int(value.strip()) for value in get(key, index).split(",") if value.strip()
            )
        except ValueError:
            raise ValueError(f"{key}: требуются числовые Telegram ID") from None
        if any(value <= 0 for value in result):
            raise ValueError(f"{key}: ID должны быть положительными")
        return result

    token = get("BOT_TOKEN", 0)
    if not token or ":" not in token:
        raise ValueError("Укажите BOT_TOKEN в окружении, .env или data/text/config.txt")
    tutor_ids = ids("TUTOR_IDS", 4)
    tutor_links = tuple(
        value.strip() for value in get("TUTOR_LINKS", 2).split(",") if value.strip()
    )
    agreement_url = get("AGREEMENT_URL", 3)
    support_url = get("SUPPORT_URL", 5)
    if len(tutor_ids) != 2 or len(tutor_links) != 2:
        raise ValueError("TUTOR_IDS и TUTOR_LINKS должны содержать по два значения")
    for url in (*tutor_links, agreement_url, support_url):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Ссылки конфигурации должны быть корректными HTTP(S) URL")
    database_path = Path(get("DATABASE_PATH", default="data/database/database_shop.sqlite"))
    if not database_path.is_absolute():
        database_path = base_dir / database_path
    return Settings(
        token,
        ids("ADMIN_IDS", 1),
        tutor_ids,
        tutor_links,
        agreement_url,
        support_url,
        database_path,
    )
