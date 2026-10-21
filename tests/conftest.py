import importlib

import pytest

from database import Database


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "shop.sqlite")
    database.initialize()
    return database


def register(db, user_id=1, balance=20000):
    db.start_captcha(user_id, "panda")
    db.solve_captcha(user_id, "panda")
    db.register(user_id, None)
    with db.connection(write=True) as conn:
        conn.execute("UPDATE users SET balance=? WHERE tg_id=?", (balance, user_id))


@pytest.fixture
def app(monkeypatch, tmp_path):
    for key, value in {
        "BOT_TOKEN": "123456789:TEST_TOKEN_NOT_A_REAL_SECRET",
        "ADMIN_IDS": "900",
        "TUTOR_IDS": "901,902",
        "TUTOR_LINKS": "https://example.com/one,https://example.com/two",
        "AGREEMENT_URL": "https://example.com/agreement",
        "SUPPORT_URL": "https://example.com/support",
        "DATABASE_PATH": str(tmp_path / "app.sqlite"),
    }.items():
        monkeypatch.setenv(key, value)
    loader = importlib.import_module("loader")
    importlib.import_module("handlers")
    monkeypatch.setattr(loader.db, "path", tmp_path / "app.sqlite")
    loader.db.initialize()
    return loader
