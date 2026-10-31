import pytest
from aiogram.methods import (
    AnswerCallbackQuery,
    DeleteMessage,
    EditMessageMedia,
    EditMessageText,
    SendMessage,
    SendPhoto,
)

from database import Database
from tests.conftest import register
from tests.test_handlers import Client


def screen(client, user_id=1):
    current = client.app.db.ui_message(user_id)
    return client.session.messages[(user_id, current["message_id"])]


@pytest.mark.asyncio
async def test_text_navigation_reuses_one_message_and_same_screen_click(app):
    register(app.db)
    client = Client(app)
    await client.send(1, "/start")
    original = screen(client).message_id
    for callback in (
        "profile",
        "back_to_profile",
        "creature_market",
        "celestial_guardians_collection",
        "back_to_market",
        "maintenance",
        "back_to_profile",
        "back_to_profile",
    ):
        await client.send(1, callback=callback)
        assert screen(client).message_id == original
    assert sum(isinstance(call, SendMessage) for call in client.session.calls) == 1
    assert len(client.session.messages) == 1


@pytest.mark.asyncio
async def test_photos_edit_in_place_and_return_to_text_removes_exact_photo(app):
    register(app.db)
    client = Client(app)
    await client.send(1, "/start")
    original = screen(client).message_id
    await client.send(1, callback="market/1")
    assert screen(client).message_id == original
    assert screen(client).photo
    await client.send(1, callback="market/2")
    assert screen(client).message_id == original
    await client.send(1, callback="back_to_celestialguardians")
    assert screen(client).message_id != original
    assert not screen(client).photo
    assert len(client.session.messages) == 1
    deleted = [call.message_id for call in client.session.calls if isinstance(call, DeleteMessage)]
    assert deleted == [original]
    assert sum(isinstance(call, EditMessageMedia) for call in client.session.calls) == 2
    assert not any(isinstance(call, SendPhoto) for call in client.session.calls)


@pytest.mark.asyncio
async def test_deleted_panel_is_recreated_once(app):
    register(app.db)
    client = Client(app)
    await client.send(1, "/start")
    original = screen(client).message_id
    client.session.messages.clear()
    await client.send(1, "/menu")
    assert screen(client).message_id != original
    assert len(client.session.messages) == 1
    await client.send(1, "/menu")
    assert sum(isinstance(call, SendMessage) for call in client.session.calls) == 2


@pytest.mark.asyncio
async def test_restart_preserves_screen_and_input_continues_in_same_message(app, monkeypatch):
    from handlers.users import navigation

    register(app.db)
    client = Client(app)
    await client.send(1, "/start")
    await client.send(1, callback="deposit")
    original = screen(client).message_id
    restarted = Database(app.db.path)
    restarted.initialize()
    monkeypatch.setattr(navigation, "db", restarted)
    await client.send(1, "invalid")
    assert screen(client).message_id == original
    assert app.db.session(1)[0] == "depositing"
    await client.send(1, "100")
    assert screen(client).message_id == original
    assert "100 RUB" in screen(client).text
    assert app.db.session(1) == ("deposit_ready", {"amount": 100})
    assert sum(isinstance(call, SendMessage) for call in client.session.calls) == 1


@pytest.mark.asyncio
async def test_callback_error_uses_alert_without_replacing_screen(app):
    register(app.db)
    client = Client(app)
    await client.send(1, "/start")
    original = screen(client)
    await client.send(1, callback="buy/invalid")
    assert screen(client) == original
    alert = client.session.calls[-1]
    assert isinstance(alert, AnswerCallbackQuery)
    assert alert.show_alert
    assert sum(isinstance(call, SendMessage) for call in client.session.calls) == 1


@pytest.mark.asyncio
async def test_edit_failure_never_creates_a_duplicate_panel(app):
    register(app.db)
    client = Client(app)
    await client.send(1, "/start")
    original = screen(client)
    client.session.fail_next_message = True
    await client.send(1, callback="profile")
    assert screen(client) == original
    client.session.edit_error = "can't parse entities"
    await client.send(1, callback="profile")
    assert screen(client) == original
    assert sum(isinstance(call, SendMessage) for call in client.session.calls) == 1
    await client.send(1, callback="profile")
    assert screen(client).message_id == original.message_id


@pytest.mark.asyncio
async def test_failed_photo_to_text_replacement_preserves_photo(app):
    register(app.db)
    client = Client(app)
    await client.send(1, "/start")
    await client.send(1, callback="market/1")
    original = screen(client)
    client.session.fail_next_message = True
    await client.send(1, callback="back_to_profile")
    assert screen(client) == original
    assert not any(isinstance(call, DeleteMessage) for call in client.session.calls)


@pytest.mark.asyncio
async def test_users_have_independent_panels(app):
    register(app.db, 1)
    register(app.db, 2)
    client = Client(app)
    await client.send(1, "/start")
    await client.send(2, "/start")
    second = screen(client, 2)
    await client.send(1, callback="profile")
    assert screen(client, 2) == second
    assert len(client.session.messages) == 2
    assert isinstance(client.session.calls[-2], EditMessageText)
    assert client.session.calls[-2].chat_id == 1


@pytest.mark.asyncio
async def test_legacy_callback_adopts_only_bot_message_and_keeps_other_messages(app):
    register(app.db)
    client = Client(app)
    # A report sent outside the navigation panel must not be removed.
    report = await client.bot.send_message(1, "Report")
    await client.send(1, callback="profile")
    original = screen(client).message_id
    assert original != report.message_id
    assert sum(isinstance(call, SendMessage) for call in client.session.calls) == 1
    await client.send(1, callback="market/1")
    await client.send(1, callback="back_to_profile")
    assert (1, report.message_id) in client.session.messages
    deleted = [call.message_id for call in client.session.calls if isinstance(call, DeleteMessage)]
    assert deleted == [original]


@pytest.mark.asyncio
async def test_database_failure_can_still_report_error(app, monkeypatch):
    import sqlite3

    client = Client(app)

    def unavailable(*args):
        raise sqlite3.OperationalError("simulated offline")

    monkeypatch.setattr(app.db, "user", unavailable)
    monkeypatch.setattr(app.db, "ui_message", unavailable)
    await client.send(1, "/start")
    assert isinstance(client.session.calls[-1], SendMessage)
