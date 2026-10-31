import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from database import Database, OperationError, amount
from tests.conftest import register


def buy(db, user_id=1, creature_id=1):
    token = db.offer(user_id, creature_id, "buy")
    db.trade(user_id, token, "buy")
    return token


def test_registration_requires_personal_captcha_and_is_idempotent(db):
    db.start_captcha(1, "a")
    db.start_captcha(2, "b")
    with pytest.raises(OperationError):
        db.register(1, None)
    with pytest.raises(OperationError):
        db.solve_captcha(1, "b")
    db.solve_captcha(1, "a")
    assert db.register(1, None)
    assert not db.register(1, "changed")
    assert db.owned(1) == []
    assert db.user(1)["username"] == "UNKNOWN"
    assert db.session(2) == ("captcha", {"emoji": "b"})


def test_trade_cycle_rejects_replays_across_repurchase(db):
    register(db)
    token = buy(db)
    assert db.user(1)["balance"] == 15000
    assert db.owned(1) == [1]
    with pytest.raises(OperationError):
        db.trade(1, token, "buy")
    sale = db.offer(1, 1, "sell")
    stale_sale = db.offer(1, 1, "sell")
    assert db.trade(1, sale, "sell") == 5000
    assert db.user(1)["balance"] == 20000
    assert db.owned(1) == []
    buy(db)
    for old in (sale, stale_sale):
        with pytest.raises(OperationError):
            db.trade(1, old, "sell")
    assert db.user(1)["balance"] == 15000
    assert db.owned(1) == [1]


def test_sell_requires_ownership_and_token_owner(db):
    register(db, 1)
    register(db, 2)
    sale = db.offer(1, 1, "sell")
    with pytest.raises(OperationError):
        db.trade(1, sale, "sell")
    token = db.offer(1, 1, "buy")
    with pytest.raises(OperationError):
        db.trade(2, token, "buy")
    with pytest.raises(OperationError):
        db.trade(1, token, "sell")
    assert db.user(1)["balance"] == db.user(2)["balance"] == 20000


def test_changed_or_deleted_catalog_item_never_charges(db):
    register(db)
    token = db.offer(1, 1, "buy")
    with db.connection(write=True) as conn:
        conn.execute("UPDATE creatures SET price=1 WHERE id=1")
    with pytest.raises(OperationError):
        db.trade(1, token, "buy")
    with db.connection(write=True) as conn:
        conn.execute("DELETE FROM creatures WHERE id=1")
    with pytest.raises(OperationError):
        db.trade(1, token, "buy")
    assert db.user(1)["balance"] == 20000


def test_insufficient_balance_and_expired_offer(db):
    register(db, balance=4999)
    token = db.offer(1, 1, "buy")
    with pytest.raises(OperationError):
        db.trade(1, token, "buy")
    with db.connection(write=True) as conn:
        conn.execute("UPDATE operations SET created=0 WHERE token=?", (token,))
    with pytest.raises(OperationError):
        db.trade(1, token, "buy")
    assert db.owned(1) == []


def test_transaction_rolls_back_inventory_balance_and_operation(db):
    register(db)
    token = db.offer(1, 1, "buy")
    with db.connection(write=True) as conn:
        conn.execute("""CREATE TRIGGER fail_balance BEFORE UPDATE OF balance ON users
                        BEGIN SELECT RAISE(ABORT, 'simulated failure'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        db.trade(1, token, "buy")
    assert db.owned(1) == []
    assert db.user(1)["balance"] == 20000
    with db.connection() as conn:
        assert (
            conn.execute("SELECT completed FROM operations WHERE token=?", (token,)).fetchone()[0]
            == 0
        )


def test_concurrent_purchases_cannot_overdraw(db):
    register(db, balance=5000)
    tokens = [db.offer(1, creature_id, "buy") for creature_id in (1, 2)]

    def purchase(token):
        try:
            db.trade(1, token, "buy")
            return True
        except OperationError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(purchase, tokens)) == [False, True]
    assert db.user(1)["balance"] == 0
    assert len(db.owned(1)) == 1


def test_concurrent_sale_replay_credits_once(db):
    register(db)
    buy(db)
    token = db.offer(1, 1, "sell")

    def sell(_):
        try:
            db.trade(1, token, "sell")
            return True
        except OperationError:
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(sell, range(4))) == 1
    assert db.user(1)["balance"] == 20000


@pytest.mark.parametrize("value", ["", "0", "-1", "1.2", "1e6", "²", "１２", "9" * 4000])
def test_amount_validation(value):
    with pytest.raises(OperationError):
        amount(value)


def test_independent_persistent_deposit_and_withdrawal(db):
    register(db, 1)
    register(db, 2)
    db.begin_flow(1, "depositing")
    db.begin_flow(2, "outputmoney")
    db.set_amount(1, "100", "depositing")
    db.set_amount(2, "200", "outputmoney")
    restarted = Database(db.path)
    restarted.initialize()
    assert restarted.session(1) == ("deposit_ready", {"amount": 100})
    assert restarted.session(2) == ("requisites", {"amount": 200})
    restarted.request_withdrawal(2, "test-card", 901)
    data = restarted.session(2)[1]
    assert restarted.confirm_withdrawal(2, data["code"])
    with pytest.raises(OperationError):
        restarted.confirm_withdrawal(2, data["code"])
    assert restarted.user(2)["balance"] == 20000
    with restarted.connection() as conn:
        assert conn.execute("SELECT status FROM withdrawals").fetchone()[0] == "confirmed"
    assert len(restarted.pending_notifications()) == 2


def test_cancel_and_non_ascii_confirmation(db):
    register(db)
    db.begin_flow(1, "outputmoney")
    db.set_amount(1, "52", "outputmoney")
    db.request_withdrawal(1, "card", 901)
    assert not db.confirm_withdrawal(1, "нет")
    db.begin_flow(1, "depositing")
    db.cancel(1)
    assert db.session(1) == (None, {})
    assert db.user(1)["status"] == "default"


def test_blacklist_cannot_be_cleared_by_navigation(db):
    register(db)
    token = db.offer(1, 1, "buy")
    db.admin_command(900, (900,), "blacklist/1", 900, 1)
    for call in (
        lambda: db.cancel(1),
        lambda: db.trade(1, token, "buy"),
        lambda: db.begin_flow(1, "depositing"),
        lambda: db.register(1, None),
    ):
        with pytest.raises(OperationError):
            call()
    assert db.user(1)["status"] == "blacklist"


def test_admin_topup_is_authorized_validated_and_idempotent(db):
    register(db)
    for actor, text in [
        (1, "bi/1/100"),
        (900, "bi/1/-100"),
        (900, "bi/99/100"),
        (900, "bi/1"),
        (900, "gettable/users;DROP TABLE users"),
    ]:
        with pytest.raises(OperationError):
            db.admin_command(actor, (900,), text, actor, 1)
    db.admin_command(900, (900,), "bi/1/100", 900, 2)
    db.admin_command(900, (900,), "bi/1/100", 900, 2)
    assert db.user(1)["balance"] == 20100


def test_mediated_sale_uses_its_own_persisted_price(db):
    register(db, 1)
    register(db, 2)
    buy(db, 1)
    buy(db, 2, 2)
    with db.connection(write=True) as conn:
        conn.executemany("INSERT INTO exchanges VALUES (?, ?, '')", [(1, 1), (2, 2)])
        conn.execute("UPDATE users SET status='selling'")
    db.price_exchange(1, "7000", (901, 902))
    db.price_exchange(2, "12000", (901, 902))
    with pytest.raises(OperationError):
        db.prepare_exchange(901, (901, 902), ("a", "b"), 2, 2, 901, 1)
    db.prepare_exchange(901, (901, 902), ("a", "b"), 1, 1, 901, 2)
    db.prepare_exchange(902, (901, 902), ("a", "b"), 2, 2, 902, 3)
    restarted = Database(db.path)
    code1 = restarted.session(1)[1]["code"]
    code2 = restarted.session(2)[1]["code"]
    assert restarted.confirm_exchange(1, code1) == 7000
    assert restarted.confirm_exchange(2, code2) == 12000
    assert restarted.user(1)["balance"] == 22000
    assert restarted.user(2)["balance"] == 27000
    with pytest.raises(OperationError):
        restarted.confirm_exchange(1, code1)


def test_missing_inventory_row_is_repaired_without_data_loss(db):
    register(db)
    with db.connection(write=True) as conn:
        conn.execute("DELETE FROM user_creature WHERE user_id=1")
    before = db.user(1)
    db.initialize()
    db.initialize()
    assert db.user(1) == before
    assert db.owned(1) == []
    assert len(db.creatures()) == 47


def test_legacy_schema_migration_preserves_data_and_custom_catalog(tmp_path):
    path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE users (tg_id v PRIMARY KEY, balance v NOT NULL,
                date_regist v NOT NULL, verified v NOT NULL, number_card TEXT NOT NULL,
                username TEXT NOT NULL, status TEXT NOT NULL);
            CREATE TABLE creatures (id v PRIMARY KEY, number NOT NULL,
                collection v NOT NULL, name v NOT NULL, color v NOT NULL,
                price NOT NULL, place v NOT NULL);
            CREATE TABLE user_creature (user_id INTEGER PRIMARY KEY, creature_list TEXT);
            CREATE TABLE exchanges (user_id v NOT NULL, creature_id v NOT NULL, price v NOT NULL);
            INSERT INTO users VALUES (1, 10000, '2024-01-02', 1, 'card', 'name', 'default');
            INSERT INTO creatures VALUES (77, 4321, 'Custom', 'Custom', 'Blue', '123', 'Place');
            INSERT INTO user_creature VALUES (1, '77');
            INSERT INTO exchanges VALUES (1, 77, 456);
        """)
    database = Database(path)
    database.initialize()
    database.initialize()
    assert database.user(1)["number_card"] == "card"
    assert database.user(1)["verified"] == 1
    assert database.owned(1) == [77]
    assert len(database.creatures()) == 1
    token = database.offer(1, 77, "sell")
    assert database.trade(1, token, "sell") == 123
    assert database.user(1)["balance"] == 10123


def test_null_inventory_and_unknown_owned_ids_are_preserved(db):
    register(db)
    with db.connection(write=True) as conn:
        conn.execute("UPDATE user_creature SET creature_list=NULL WHERE user_id=1")
    buy(db)
    with db.connection(write=True) as conn:
        conn.execute("UPDATE user_creature SET creature_list='1,999' WHERE user_id=1")
    token = db.offer(1, 1, "sell")
    db.trade(1, token, "sell")
    assert db.owned(1) == [999]


def test_broken_inventory_causes_no_credit(db):
    register(db)
    with db.connection(write=True) as conn:
        conn.execute("UPDATE user_creature SET creature_list='broken' WHERE user_id=1")
    token = db.offer(1, 1, "sell")
    with pytest.raises(OperationError):
        db.trade(1, token, "sell")
    assert db.user(1)["balance"] == 20000
