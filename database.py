import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from config import BASE_DIR, MINIMUM_AMOUNT


class OperationError(ValueError):
    pass


def amount(value, minimum=1):
    text = str(value)
    if not text.isascii() or not text.isdecimal() or len(text) > 15:
        raise OperationError("Введите целое положительное число.")
    result = int(text)
    if not minimum <= result <= 10**15:
        raise OperationError(f"Минимальная сумма: {minimum} RUB.")
    return result


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def connection(self, write=False):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection(write=True) as conn:
            statements = [
                """CREATE TABLE IF NOT EXISTS users (
                    tg_id INTEGER PRIMARY KEY, balance INTEGER NOT NULL,
                    date_regist TEXT NOT NULL, verified INTEGER NOT NULL,
                    number_card TEXT NOT NULL DEFAULT '0', username TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'default')""",
                """CREATE TABLE IF NOT EXISTS creatures (
                    id INTEGER PRIMARY KEY, number INTEGER NOT NULL,
                    collection TEXT NOT NULL, name TEXT NOT NULL, color TEXT NOT NULL,
                    price INTEGER NOT NULL, place TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS user_creature (
                    user_id INTEGER PRIMARY KEY, creature_list TEXT)""",
                """CREATE TABLE IF NOT EXISTS exchanges (
                    user_id INTEGER NOT NULL, creature_id INTEGER NOT NULL, price TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS sessions (
                    user_id INTEGER PRIMARY KEY, state TEXT NOT NULL, data TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS ui_messages (
                    chat_id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL,
                    kind TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS operations (
                    token TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
                    creature_id INTEGER NOT NULL, action TEXT NOT NULL,
                    price INTEGER NOT NULL, created REAL NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0)""",
                """CREATE TABLE IF NOT EXISTS processed_messages (
                    chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL,
                    PRIMARY KEY (chat_id, message_id))""",
                """CREATE TABLE IF NOT EXISTS withdrawals (
                    id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, amount INTEGER NOT NULL,
                    requisites TEXT NOT NULL, status TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS outbox (
                    id INTEGER PRIMARY KEY, chat_id INTEGER NOT NULL, text TEXT NOT NULL,
                    sent INTEGER NOT NULL DEFAULT 0)""",
            ]
            catalog_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='creatures'"
            ).fetchone()
            for statement in statements:
                conn.execute(statement)
            if not catalog_exists:
                catalog = json.loads(
                    (BASE_DIR / "data/text/catalog.json").read_text(encoding="utf-8")
                )
                conn.executemany("INSERT INTO creatures VALUES (?, ?, ?, ?, ?, ?, ?)", catalog)
            conn.execute("""INSERT OR IGNORE INTO user_creature (user_id, creature_list)
                            SELECT tg_id, '' FROM users""")

    @staticmethod
    def _user(conn, user_id):
        row = conn.execute("SELECT * FROM users WHERE tg_id=?", (user_id,)).fetchone()
        if row is None:
            raise OperationError("Для создания профиля напишите /start.")
        if row["status"] == "blacklist":
            raise OperationError("Вы в чёрном списке. Доступ к боту запрещён.")
        return row

    def ui_message(self, chat_id: int):
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM ui_messages WHERE chat_id=?", (chat_id,)).fetchone()
            return dict(row) if row else None

    def save_ui_message(self, chat_id: int, message_id: int, kind: str):
        with self.connection(write=True) as conn:
            conn.execute(
                """INSERT INTO ui_messages VALUES (?, ?, ?)
                   ON CONFLICT(chat_id) DO UPDATE SET
                       message_id=excluded.message_id, kind=excluded.kind""",
                (chat_id, message_id, kind),
            )

    def user(self, user_id):
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE tg_id=?", (user_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _owned(conn, user_id):
        row = conn.execute(
            "SELECT creature_list FROM user_creature WHERE user_id=?", (user_id,)
        ).fetchone()
        try:
            return (
                [int(value.strip()) for value in (row[0] or "").split(",") if value.strip()]
                if row
                else []
            )
        except ValueError:
            raise OperationError("Коллекция повреждена. Обратитесь в поддержку.") from None

    @staticmethod
    def _save_owned(conn, user_id, owned):
        conn.execute(
            """INSERT INTO user_creature VALUES (?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET creature_list=excluded.creature_list""",
            (user_id, ",".join(map(str, owned))),
        )

    def owned(self, user_id):
        with self.connection() as conn:
            self._user(conn, user_id)
            return self._owned(conn, user_id)

    def creatures(self, collection=None):
        with self.connection() as conn:
            if collection is None:
                rows = conn.execute("SELECT * FROM creatures ORDER BY id")
            else:
                rows = conn.execute(
                    "SELECT * FROM creatures WHERE collection=? ORDER BY id", (collection,)
                )
            return [dict(row) for row in rows]

    def creature(self, creature_id):
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM creatures WHERE id=?", (creature_id,)).fetchone()
            if row is None:
                raise OperationError("Creature больше не доступен. Откройте маркет заново.")
            return dict(row)

    @staticmethod
    def _session(conn, user_id):
        row = conn.execute(
            "SELECT state, data FROM sessions WHERE user_id=?", (user_id,)
        ).fetchone()
        return (row[0], json.loads(row[1])) if row else (None, {})

    @staticmethod
    def _set_session(conn, user_id, state, data):
        conn.execute(
            """INSERT INTO sessions VALUES (?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, data=excluded.data""",
            (user_id, state, json.dumps(data)),
        )

    def session(self, user_id):
        with self.connection() as conn:
            return self._session(conn, user_id)

    def start_captcha(self, user_id, emoji):
        with self.connection(write=True) as conn:
            self._set_session(conn, user_id, "captcha", {"emoji": emoji})

    def solve_captcha(self, user_id, emoji):
        with self.connection(write=True) as conn:
            state, data = self._session(conn, user_id)
            if state != "captcha" or data.get("emoji") != emoji:
                raise OperationError("Капча пройдена неверно или устарела. Напишите /start.")
            self._set_session(conn, user_id, "agreement", {})

    def register(self, user_id, username):
        with self.connection(write=True) as conn:
            if conn.execute("SELECT 1 FROM users WHERE tg_id=?", (user_id,)).fetchone():
                self._user(conn, user_id)
                return False
            if self._session(conn, user_id)[0] != "agreement":
                raise OperationError("Сначала пройдите капчу: /start.")
            conn.execute(
                "INSERT INTO users VALUES (?, 0, ?, 0, '0', ?, 'default')",
                (user_id, date.today().isoformat(), username or "UNKNOWN"),
            )
            self._save_owned(conn, user_id, [])
            conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            return True

    def begin_flow(self, user_id, state):
        if state not in {"depositing", "outputmoney"}:
            raise ValueError("Unknown flow")
        with self.connection(write=True) as conn:
            self._user(conn, user_id)
            self._cancel(conn, user_id)
            self._set_session(conn, user_id, state, {})
            conn.execute("UPDATE users SET status=? WHERE tg_id=?", (state, user_id))

    @staticmethod
    def _cancel(conn, user_id):
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        conn.execute(
            "UPDATE users SET status='default' WHERE tg_id=? AND status!='blacklist'", (user_id,)
        )
        conn.execute(
            "UPDATE withdrawals SET status='cancelled' WHERE user_id=? AND status='awaiting_code'",
            (user_id,),
        )

    def cancel(self, user_id):
        with self.connection(write=True) as conn:
            self._user(conn, user_id)
            self._cancel(conn, user_id)

    def set_amount(self, user_id, value, expected_state):
        if expected_state not in {"depositing", "outputmoney"}:
            raise ValueError("Unknown amount state")
        value = amount(value, MINIMUM_AMOUNT)
        with self.connection(write=True) as conn:
            user = self._user(conn, user_id)
            if self._session(conn, user_id)[0] != expected_state:
                raise OperationError("Запрос устарел. Начните операцию заново.")
            if expected_state == "outputmoney" and int(user["balance"]) < value:
                raise OperationError("Сумма вывода превышает баланс.")
            next_state = "deposit_ready" if expected_state == "depositing" else "requisites"
            self._set_session(conn, user_id, next_state, {"amount": value})
            conn.execute(
                "UPDATE users SET status=? WHERE tg_id=?",
                ("default" if expected_state == "depositing" else next_state, user_id),
            )
        return value

    def offer(self, user_id, creature_id, action):
        if action not in {"buy", "sell"}:
            raise ValueError("Unknown action")
        with self.connection(write=True) as conn:
            self._user(conn, user_id)
            row = conn.execute("SELECT price FROM creatures WHERE id=?", (creature_id,)).fetchone()
            if row is None:
                raise OperationError("Creature не найден.")
            price = amount(row[0])
            token = secrets.token_hex(12)
            conn.execute(
                "INSERT INTO operations VALUES (?, ?, ?, ?, ?, ?, 0)",
                (token, user_id, creature_id, action, price, time.time()),
            )
            return token

    def trade(self, user_id, token, action):
        with self.connection(write=True) as conn:
            user = self._user(conn, user_id)
            operation = conn.execute("SELECT * FROM operations WHERE token=?", (token,)).fetchone()
            if not operation or operation["user_id"] != user_id or operation["action"] != action:
                raise OperationError("Кнопка устарела. Откройте Creature заново.")
            if operation["completed"]:
                raise OperationError("Эта операция уже выполнена.")
            if time.time() - operation["created"] > 86400:
                raise OperationError("Кнопка устарела. Откройте Creature заново.")
            creature_id = operation["creature_id"]
            row = conn.execute("SELECT price FROM creatures WHERE id=?", (creature_id,)).fetchone()
            if row is None or amount(row[0]) != operation["price"]:
                raise OperationError("Цена изменилась. Откройте Creature заново.")
            price = operation["price"]
            owned = self._owned(conn, user_id)
            balance = int(user["balance"])
            if action == "buy":
                if creature_id in owned:
                    raise OperationError("Этот Creature уже есть в вашей коллекции.")
                if balance < price:
                    raise OperationError("Недостаточно средств на балансе.")
                owned.append(creature_id)
                balance -= price
            else:
                if creature_id not in owned:
                    raise OperationError("Этот Creature не принадлежит вам.")
                owned.remove(creature_id)
                balance += price
                conn.execute(
                    "DELETE FROM exchanges WHERE user_id=? AND creature_id=?",
                    (user_id, creature_id),
                )
            self._save_owned(conn, user_id, owned)
            conn.execute("UPDATE users SET balance=? WHERE tg_id=?", (balance, user_id))
            # Invalidate other buttons for this ownership cycle, including after a repurchase.
            conn.execute(
                "UPDATE operations SET completed=1 WHERE user_id=? AND creature_id=?",
                (user_id, creature_id),
            )
            return price

    def admin_command(self, actor_id, admin_ids, text, chat_id, message_id):
        if actor_id not in admin_ids:
            raise OperationError("Команда доступна только администраторам.")
        parts = text.split("/")
        command = parts[0]
        with self.connection(write=True) as conn:
            if command == "gettable":
                if len(parts) != 2 or parts[1] not in {
                    "users",
                    "creatures",
                    "user_creature",
                    "exchanges",
                }:
                    raise OperationError(
                        "Допустимые таблицы: users, creatures, user_creature, exchanges."
                    )
                rows = conn.execute(f'SELECT * FROM "{parts[1]}"').fetchall()
                return "\n".join(" | ".join(map(str, row)) for row in rows) or "Таблица пуста."
            if command == "users":
                rows = conn.execute("SELECT * FROM users ORDER BY tg_id").fetchall()
                return (
                    "\n\n".join(
                        f"Профиль: #{row['tg_id']}\nБаланс: {row['balance']} RUB\n"
                        f"Верификация: {bool(row['verified'])}\nНомер карты: {row['number_card']}\n"
                        f"Username: @{row['username']}\nСтатус: {row['status']}"
                        for row in rows
                    )
                    or "Пользователей пока нет."
                )
            if len(parts) != (3 if command == "bi" else 2):
                raise OperationError("Неверный формат команды. Справка: /admin.")
            user_id = amount(parts[1])
            user = conn.execute("SELECT * FROM users WHERE tg_id=?", (user_id,)).fetchone()
            if user is None:
                raise OperationError("Пользователь не найден.")
            if command in {"creature", "createre"}:
                owned = self._owned(conn, user_id)
                details = []
                for creature_id in owned:
                    item = conn.execute(
                        "SELECT * FROM creatures WHERE id=?", (creature_id,)
                    ).fetchone()
                    if item:
                        details.append(
                            f"Creature id: {creature_id}\nНомер: {item['number']}\n"
                            f"Коллекция: {item['collection']}\nНазвание: {item['name']}\n"
                            f"Цвет: {item['color']}\nЦена: {item['price']} RUB"
                        )
                    else:
                        details.append(f"Creature id: {creature_id} (отсутствует в каталоге)")
                return f"Профиль: #{user_id}\n\n" + ("\n\n".join(details) or "Creatures: нет")
            if command not in {"bi", "verify", "blacklist"}:
                raise OperationError("Неизвестная команда.")
            if conn.execute(
                "SELECT 1 FROM processed_messages WHERE chat_id=? AND message_id=?",
                (chat_id, message_id),
            ).fetchone():
                return "Эта команда уже выполнена."
            if command == "bi":
                value = amount(parts[2])
                conn.execute(
                    "UPDATE users SET balance=? WHERE tg_id=?",
                    (int(user["balance"]) + value, user_id),
                )
                result = "Баланс успешно пополнен✅"
            elif command == "verify":
                conn.execute("UPDATE users SET verified=1 WHERE tg_id=?", (user_id,))
                result = "Пользователь верифицирован✅"
            else:
                if user_id in admin_ids:
                    raise OperationError("Нельзя добавить администратора в чёрный список.")
                status = "default" if user["status"] == "blacklist" else "blacklist"
                self._cancel(conn, user_id)
                conn.execute("UPDATE users SET status=? WHERE tg_id=?", (status, user_id))
                result = (
                    "Пользователь в чёрном списке⚫️"
                    if status == "blacklist"
                    else "Пользователь в белом списке⚪️"
                )
            conn.execute("INSERT INTO processed_messages VALUES (?, ?)", (chat_id, message_id))
            return result

    @staticmethod
    def _enqueue(conn, chat_id, text):
        conn.execute("INSERT INTO outbox (chat_id, text) VALUES (?, ?)", (chat_id, text))

    def request_withdrawal(self, user_id, requisites, tutor_id):
        requisites = requisites.strip()
        if not requisites or len(requisites) > 200:
            raise OperationError("Введите реквизиты длиной от 1 до 200 символов.")
        with self.connection(write=True) as conn:
            user = self._user(conn, user_id)
            state, data = self._session(conn, user_id)
            if state != "requisites":
                raise OperationError("Запрос устарел. Начните вывод заново.")
            value = amount(data.get("amount"), MINIMUM_AMOUNT)
            if int(user["balance"]) < value:
                raise OperationError("Сумма вывода превышает баланс.")
            request_id = secrets.token_hex(8)
            code = str(secrets.randbelow(9000) + 1000)
            conn.execute(
                "INSERT INTO withdrawals VALUES (?, ?, ?, ?, 'awaiting_code')",
                (request_id, user_id, value, requisites),
            )
            conn.execute(
                "UPDATE users SET number_card=?, status='default' WHERE tg_id=?",
                (requisites, user_id),
            )
            self._set_session(
                conn,
                user_id,
                "withdrawal_code",
                {"id": request_id, "code": code, "tutor": tutor_id},
            )
            self._enqueue(
                conn,
                tutor_id,
                f"Заявка {request_id}: пользователь {user_id}, сумма {value} RUB.\n"
                f"Реквизиты: {requisites}\nПередайте пользователю код: {code}",
            )

    def confirm_withdrawal(self, user_id, code):
        with self.connection(write=True) as conn:
            user = self._user(conn, user_id)
            state, data = self._session(conn, user_id)
            if state != "withdrawal_code":
                raise OperationError("Нет заявки для подтверждения.")
            row = conn.execute(
                "SELECT * FROM withdrawals WHERE id=? AND status='awaiting_code'", (data["id"],)
            ).fetchone()
            if row is None:
                raise OperationError("Заявка уже обработана.")
            success = (
                code.isascii()
                and secrets.compare_digest(code, data["code"])
                and int(user["balance"]) >= row["amount"]
            )
            status = "confirmed" if success else "cancelled"
            conn.execute("UPDATE withdrawals SET status=? WHERE id=?", (status, data["id"]))
            conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            self._enqueue(
                conn,
                data["tutor"],
                f"Заявка {data['id']}: {status}. Автоматическая выплата не выполнялась.",
            )
            return success

    def price_exchange(self, user_id, value, tutor_ids):
        value = amount(value)
        with self.connection(write=True) as conn:
            user = self._user(conn, user_id)
            if user["status"] != "selling":
                raise OperationError("Нет активной заявки на продажу.")
            rows = conn.execute(
                "SELECT rowid, creature_id FROM exchanges WHERE user_id=? AND price=''", (user_id,)
            ).fetchall()
            if len(rows) != 1 or int(rows[0]["creature_id"]) not in self._owned(conn, user_id):
                raise OperationError(
                    "Заявка на продажу отсутствует или неоднозначна. Обратитесь в поддержку."
                )
            creature_id = int(rows[0]["creature_id"])
            conn.execute("UPDATE exchanges SET price=? WHERE rowid=?", (value, rows[0]["rowid"]))
            conn.execute("UPDATE users SET status='default' WHERE tg_id=?", (user_id,))
            tutor_id = tutor_ids[0 if value <= 10000 else 1]
            self._enqueue(
                conn,
                tutor_id,
                f"Пользователь {user_id} продаёт Creature {creature_id} за {value} RUB.\n"
                f"Для подтверждения отправьте: {user_id},{creature_id}",
            )

    def prepare_exchange(
        self, tutor_id, tutor_ids, tutor_links, user_id, creature_id, chat_id, message_id
    ):
        with self.connection(write=True) as conn:
            self._user(conn, user_id)
            rows = conn.execute(
                "SELECT price FROM exchanges WHERE user_id=? AND creature_id=?",
                (user_id, creature_id),
            ).fetchall()
            if len(rows) != 1 or creature_id not in self._owned(conn, user_id):
                raise OperationError("Действующая заявка на продажу не найдена.")
            price = amount(rows[0]["price"])
            index = 0 if price <= 10000 else 1
            if tutor_id != tutor_ids[index]:
                raise OperationError("Эта заявка относится к другому куратору.")
            if conn.execute(
                "SELECT 1 FROM processed_messages WHERE chat_id=? AND message_id=?",
                (chat_id, message_id),
            ).fetchone():
                return
            state, _ = self._session(conn, user_id)
            if state is not None:
                raise OperationError("У пользователя уже открыт диалог. Сначала завершите его.")
            code = str(secrets.randbelow(9000) + 1000)
            self._set_session(
                conn,
                user_id,
                "sale_code",
                {"creature_id": creature_id, "price": price, "code": code},
            )
            conn.execute("INSERT INTO processed_messages VALUES (?, ?)", (chat_id, message_id))
            self._enqueue(conn, tutor_id, f"Передайте продавцу {user_id} код: {code}")
            self._enqueue(
                conn,
                user_id,
                f"Нашли покупателя. Свяжитесь с куратором: {tutor_links[index]}\nВведите код подтверждения продажи.",
            )

    def confirm_exchange(self, user_id, code):
        with self.connection(write=True) as conn:
            user = self._user(conn, user_id)
            state, data = self._session(conn, user_id)
            if state != "sale_code":
                raise OperationError("Нет продажи для подтверждения.")
            if not code.isascii() or not secrets.compare_digest(code, data["code"]):
                conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
                return None
            rows = conn.execute(
                "SELECT price FROM exchanges WHERE user_id=? AND creature_id=?",
                (user_id, data["creature_id"]),
            ).fetchall()
            owned = self._owned(conn, user_id)
            if (
                len(rows) != 1
                or amount(rows[0][0]) != data["price"]
                or data["creature_id"] not in owned
            ):
                raise OperationError("Заявка на продажу устарела.")
            owned.remove(data["creature_id"])
            self._save_owned(conn, user_id, owned)
            conn.execute(
                "UPDATE users SET balance=? WHERE tg_id=?",
                (int(user["balance"]) + data["price"], user_id),
            )
            conn.execute(
                "DELETE FROM exchanges WHERE user_id=? AND creature_id=?",
                (user_id, data["creature_id"]),
            )
            conn.execute(
                "UPDATE operations SET completed=1 WHERE user_id=? AND creature_id=?",
                (user_id, data["creature_id"]),
            )
            conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            return data["price"]

    def pending_notifications(self):
        with self.connection() as conn:
            return [
                dict(row)
                for row in conn.execute("SELECT * FROM outbox WHERE sent=0 ORDER BY id LIMIT 50")
            ]

    def mark_notification_sent(self, notification_id):
        with self.connection(write=True) as conn:
            conn.execute("UPDATE outbox SET sent=1 WHERE id=?", (notification_id,))
