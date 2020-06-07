from arango.database import StandardDatabase
from passlib.context import CryptContext
from schoolsyst_api.accounts.auth import (
    JWT_SUB_FORMAT,
    analyze_password,
    authenticate_user,
    extract_username_from_jwt_payload,
    hash_password,
    is_password_strong_enough,
    verify_password,
)
from tests import database_mock, mocks
from tests.mocks import JOHN_PASSWORD
from zxcvbn import zxcvbn


def test_is_password_strong_enough():
    assert is_password_strong_enough({"score": 4})
    assert is_password_strong_enough({"score": 3})
    assert is_password_strong_enough({"score": 2})
    assert not is_password_strong_enough({"score": 1})
    assert not is_password_strong_enough({"score": 0})


def test_analyze_password():
    actual = analyze_password("hunter2", "ewen-lbh", "hey@ewen.werks")
    expected = zxcvbn("hunter2", ["ewen-lbh", "hey@ewen.werks"])
    del actual["calc_time"]
    del expected["calc_time"]
    assert actual == expected


def test_verify_password():
    assert verify_password(
        "correct-battery-horse-staple",
        "$argon2id$v=19$m=102400,t=2,p=8$h/Bea41xjlEqBQAgpPTemw$tprEaXUjIeEP+B9ryxSVAw",
    )
    assert not verify_password(
        "correct-battery-horse-staple",
        "$argon2id$v=19$m=102400,t=2,p=8$h/Bea41xjlEqBQAgpkTemw$tprEaXUjIeEP+B9ryxSVAw",
    )
    assert not verify_password("correct-battery-horse-staple", "hunter2")


def test_hash_password():
    assert (
        hash_password("hunter2")[:20]
        == CryptContext(schemes=["argon2"], deprecated="auto").hash("hunter2")[:20]
    )


def test_extract_username_from_jwt_payload():
    assert extract_username_from_jwt_payload({"sub": None}) is None
    assert extract_username_from_jwt_payload({}) is None
    assert extract_username_from_jwt_payload({"sub": "ewen-lbh"}) is None
    assert (
        extract_username_from_jwt_payload({"sub": JWT_SUB_FORMAT.format("ewen-lbh")})
        == "ewen-lbh"
    )


def test_authenticate_user():
    with database_mock() as db:
        db: StandardDatabase
        db.collection("users").insert(mocks.users.john.json(by_alias=True))
        db.collection("users").insert(mocks.users.alice.json(by_alias=True))

        assert not authenticate_user(db, username="hahah", password="hmmmmmm")
        assert not authenticate_user(
            db, username=mocks.users.john.username, password="not john's password"
        )
        assert (
            authenticate_user(
                db, username=mocks.users.john.username, password=JOHN_PASSWORD
            )
            == mocks.users.john
        )
