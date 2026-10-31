from datetime import UTC, datetime

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import (
    AnswerCallbackQuery,
    DeleteMessage,
    EditMessageMedia,
    EditMessageText,
    SendMessage,
    SendPhoto,
)
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, Update, User

from main import deliver_notifications
from tests.conftest import register


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.fail_next_message = False
        self.messages = {}
        self.edit_error = None

    async def close(self):
        return None

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        if isinstance(method, (SendMessage, SendPhoto, EditMessageText, EditMessageMedia)):
            if self.fail_next_message:
                self.fail_next_message = False
                raise TelegramNetworkError(method=method, message="simulated offline")
            editing = isinstance(method, (EditMessageText, EditMessageMedia))
            message_id = method.message_id if editing else 1000 + len(self.calls)
            key = (int(method.chat_id), message_id)
            if editing:
                if self.edit_error:
                    error, self.edit_error = self.edit_error, None
                    raise TelegramBadRequest(method=method, message=error)
                if key not in self.messages:
                    raise TelegramBadRequest(method=method, message="message to edit not found")
                old = self.messages[key]
                if isinstance(method, EditMessageText) and old.photo:
                    raise TelegramBadRequest(
                        method=method, message="there is no text in the message to edit"
                    )
                if (
                    isinstance(method, EditMessageText)
                    and old.text == method.text
                    and old.reply_markup == method.reply_markup
                ):
                    raise TelegramBadRequest(method=method, message="message is not modified")
            photo = isinstance(method, (SendPhoto, EditMessageMedia))
            result = Message(
                message_id=message_id,
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                from_user=User(id=bot.id, is_bot=True, first_name="Bot"),
                text=getattr(method, "text", None),
                caption=method.media.caption
                if isinstance(method, EditMessageMedia)
                else getattr(method, "caption", None),
                photo=[PhotoSize(file_id="photo", file_unique_id="photo", width=100, height=100)]
                if photo
                else None,
                reply_markup=method.reply_markup,
            )
            self.messages[key] = result
            return result
        if isinstance(method, DeleteMessage):
            key = (int(method.chat_id), method.message_id)
            if key not in self.messages:
                raise TelegramBadRequest(method=method, message="message to delete not found")
            del self.messages[key]
        return True

    async def stream_content(self, url, **kwargs):
        yield b""


class Client:
    def __init__(self, app):
        self.app = app
        self.session = FakeSession()
        self.bot = Bot("123456789:TEST_TOKEN_NOT_A_REAL_SECRET", session=self.session)
        self.sequence = 0

    async def send(self, user_id, text=None, callback=None, chat_id=None):
        self.sequence += 1
        user = User(id=user_id, is_bot=False, first_name="Tester")
        message = Message(
            message_id=self.sequence,
            date=datetime.now(UTC),
            chat=Chat(id=chat_id or user_id, type="private"),
            from_user=user,
            text=text,
        )
        if callback is None:
            update = Update(update_id=self.sequence, message=message)
        else:
            screen = self.app.db.ui_message(message.chat.id)
            if screen and (message.chat.id, screen["message_id"]) in self.session.messages:
                message = self.session.messages[(message.chat.id, screen["message_id"])]
            else:
                message = message.model_copy(
                    update={
                        "from_user": User(id=self.bot.id, is_bot=True, first_name="Bot"),
                    }
                )
                self.session.messages[(message.chat.id, message.message_id)] = message
            query = CallbackQuery(
                id=str(self.sequence),
                from_user=user,
                chat_instance="test",
                message=message,
                data=callback,
            )
            update = Update(update_id=self.sequence, callback_query=query)
        await self.app.dp.feed_update(self.bot, update)
        return self.session.calls


@pytest.mark.asyncio
async def test_complete_registration_profile_and_trade_scenario(app):
    client = Client(app)
    await client.send(1, "/start")
    emoji = app.db.session(1)[1]["emoji"]
    await client.send(1, callback=emoji)
    await client.send(1, callback="user_acceptation")
    assert app.db.user(1) is not None
    await client.send(900, "bi/1/10000")
    await client.send(1, callback="creature_market")
    await client.send(1, callback="celestial_guardians_collection")
    calls = await client.send(1, callback="market/1")
    photo = next(
        call for call in reversed(calls) if isinstance(call, (SendPhoto, EditMessageMedia))
    )
    buy_callback = photo.reply_markup.inline_keyboard[0][1].callback_data
    assert buy_callback.startswith("buy/")
    assert len(buy_callback.encode()) <= 64
    await client.send(1, callback=buy_callback)
    await client.send(1, callback=buy_callback)
    assert app.db.owned(1) == [1]
    assert app.db.user(1)["balance"] == 5000
    await client.send(1, callback="my_creature")
    calls = await client.send(1, callback="m/1")
    photo = next(
        call for call in reversed(calls) if isinstance(call, (SendPhoto, EditMessageMedia))
    )
    sale_callback = photo.reply_markup.inline_keyboard[0][1].callback_data
    await client.send(1, callback=sale_callback)
    await client.send(1, callback=sale_callback)
    assert app.db.owned(1) == []
    assert app.db.user(1)["balance"] == 10000
    assert sum(isinstance(call, AnswerCallbackQuery) for call in calls) == 11


@pytest.mark.asyncio
async def test_two_users_deposit_amounts_and_cancel(app):
    client = Client(app)
    register(app.db, 1)
    register(app.db, 2)
    await client.send(1, callback="deposit")
    await client.send(2, callback="deposit")
    await client.send(1, "100")
    await client.send(2, "200")
    calls = await client.send(1, callback="way_to_increase_balance_bankcard")
    screen = next(
        call for call in reversed(calls) if isinstance(call, (SendMessage, EditMessageText))
    )
    assert "100 RUB" in screen.text
    assert "200 RUB" not in screen.text
    calls = await client.send(2, callback="way_to_increase_balance_bankcard")
    screen = next(
        call for call in reversed(calls) if isinstance(call, (SendMessage, EditMessageText))
    )
    assert "200 RUB" in screen.text
    await client.send(1, "Меню🌐")
    assert app.db.session(1) == (None, {})
    assert app.db.session(2)[0] == "deposit_ready"


@pytest.mark.asyncio
async def test_withdrawal_flow_does_not_execute_payment(app):
    client = Client(app)
    register(app.db)
    await client.send(1, callback="output_money")
    await client.send(1, "52")
    await client.send(1, "card <test>")
    data = app.db.session(1)[1]
    await client.send(1, data["code"])
    assert app.db.user(1)["balance"] == 20000
    assert app.db.session(1) == (None, {})
    await deliver_notifications(client.bot, app.db)
    sent = [
        call
        for call in client.session.calls
        if isinstance(call, SendMessage) and call.chat_id == 901
    ]
    assert len(sent) == 2
    assert all(call.parse_mode is None for call in sent)


@pytest.mark.asyncio
async def test_blacklisted_navigation_and_unknown_users(app):
    client = Client(app)
    register(app.db)
    app.db.admin_command(900, (900,), "blacklist/1", 900, 1)
    for callback in (
        "back_to_profile",
        "back_to_profile2",
        "market/1",
        "sell/1/1",
        "user_acceptation",
    ):
        await client.send(1, callback=callback)
    await client.send(1, "Меню🌐")
    assert app.db.user(1)["status"] == "blacklist"
    assert app.db.user(1)["balance"] == 20000
    calls = await client.send(5, callback="profile")
    assert "/start" in calls[-1].text
    await client.send(5, callback="user_acceptation")
    assert app.db.user(5) is None


@pytest.mark.asyncio
async def test_invalid_callbacks_nontext_and_wrong_chat(app):
    client = Client(app)
    register(app.db)
    for callback in ("buy/1/-100/1", "sell/1/1", "market/bad", "market/99999", "unknown"):
        await client.send(1, callback=callback)
    await client.send(1)
    await client.send(1, callback="market/1", chat_id=2)
    assert app.db.user(1)["balance"] == 20000
    assert app.db.owned(1) == []
    assert not any(isinstance(call, SendPhoto) for call in client.session.calls)


@pytest.mark.asyncio
async def test_network_failure_after_trade_cannot_duplicate_purchase(app):
    client = Client(app)
    register(app.db)
    token = app.db.offer(1, 1, "buy")
    client.session.fail_next_message = True
    await client.send(1, callback=f"buy/{token}")
    await client.send(1, callback=f"buy/{token}")
    assert app.db.owned(1) == [1]
    assert app.db.user(1)["balance"] == 15000


@pytest.mark.asyncio
async def test_outbox_survives_external_failure_and_restart(app):
    from database import Database

    register(app.db)
    app.db.begin_flow(1, "outputmoney")
    app.db.set_amount(1, "52", "outputmoney")
    app.db.request_withdrawal(1, "card", 901)
    client = Client(app)
    client.session.fail_next_message = True
    await deliver_notifications(client.bot, app.db)
    assert len(app.db.pending_notifications()) == 1
    restarted = Database(app.db.path)
    await deliver_notifications(client.bot, restarted)
    assert restarted.pending_notifications() == []


@pytest.mark.asyncio
async def test_unavailable_callback_message_is_acknowledged(app):
    from aiogram.types import InaccessibleMessage

    client = Client(app)
    query = CallbackQuery(
        id="expired",
        from_user=User(id=1, is_bot=False, first_name="Test"),
        chat_instance="test",
        data="profile",
        message=InaccessibleMessage(chat=Chat(id=1, type="private"), message_id=1, date=0),
    )
    await app.dp.feed_update(client.bot, Update(update_id=99, callback_query=query))
    assert len(client.session.calls) == 1
    assert isinstance(client.session.calls[0], AnswerCallbackQuery)


@pytest.mark.asyncio
async def test_startup_initializes_and_closes_bot_after_polling_error(app, monkeypatch):
    import asyncio
    from unittest.mock import AsyncMock

    import main

    closed = AsyncMock()
    monkeypatch.setattr(app.bot.session, "close", closed)
    monkeypatch.setattr(app.dp, "start_polling", AsyncMock(side_effect=RuntimeError("test")))

    async def idle_worker(bot, db):
        await asyncio.Event().wait()

    monkeypatch.setattr(main, "notification_worker", idle_worker)
    with pytest.raises(RuntimeError, match="test"):
        await main.on_startup()
    closed.assert_awaited_once()
    assert app.db.creatures()


@pytest.mark.asyncio
async def test_failed_error_response_does_not_escape_middleware(app):
    client = Client(app)
    client.session.fail_next_message = True
    await client.send(777, callback="profile")
    assert app.db.user(777) is None
