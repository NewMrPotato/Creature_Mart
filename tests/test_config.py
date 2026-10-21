from pathlib import Path

import pytest

from config import load_settings


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for key in (
        "BOT_TOKEN",
        "ADMIN_IDS",
        "TUTOR_IDS",
        "TUTOR_LINKS",
        "AGREEMENT_URL",
        "SUPPORT_URL",
        "DATABASE_PATH",
    ):
        monkeypatch.delenv(key, raising=False)


def test_legacy_config_and_environment_override(tmp_path, monkeypatch):
    config = tmp_path / "data/text/config.txt"
    config.parent.mkdir(parents=True)
    config.write_text(
        "123:dummy \\ token\n1,2 \\ admins\nhttps://example.com/a,https://example.com/b \\ links\n"
        "https://example.com/agreement \\ agreement\n3,4 \\ tutors\nhttps://example.com/support \\ support\n",
        encoding="utf-8",
    )
    settings = load_settings(tmp_path)
    assert settings.admin_ids == (1, 2)
    assert settings.database_path == tmp_path / "data/database/database_shop.sqlite"
    monkeypatch.setenv("ADMIN_IDS", "9")
    monkeypatch.setenv("DATABASE_PATH", "different.sqlite")
    assert load_settings(tmp_path).admin_ids == (9,)
    assert load_settings(tmp_path).database_path == tmp_path / "different.sqlite"


def test_env_example_missing_token_has_safe_error(tmp_path):
    source = Path(__file__).resolve().parents[1] / ".env.example"
    (tmp_path / ".env").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="BOT_TOKEN"):
        load_settings(tmp_path)


def test_invalid_configuration_does_not_echo_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "secret-without-separator")
    with pytest.raises(ValueError) as error:
        load_settings(tmp_path)
    assert "secret-without-separator" not in str(error.value)
