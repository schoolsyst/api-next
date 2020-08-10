import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import nanoid
import schoolsyst_api.database
from arango.database import StandardDatabase
from fastapi.testclient import TestClient
from schoolsyst_api.accounts.auth import hash_password
from schoolsyst_api.main import api
from schoolsyst_api.models import DBUser, Subject, UsernameStr

os.environ["TESTING"] = "True"
client = TestClient(api)
ALICE_PASSWORD = "fast-unicorn-snails-dragon5"
ALICE_KEY = "8FPuamSTXK"
JOHN_PASSWORD = "dice-wears-hats9-star-game"
JOHN_KEY = "zMSLrwGwZA"


@contextmanager
def database_mock() -> StandardDatabase:
    db_name = f"mock-database-{nanoid.generate(size=5)}"
    os.environ["CURRENT_MOCK_DB_NAME"] = db_name

    print(f"[MOCK] Creating mock database {db_name}")
    db: Optional[StandardDatabase] = schoolsyst_api.database.initialize(db_name)
    if db is None:
        raise ValueError("Could not create mock database")

    try:
        yield db
    finally:
        sys_db = schoolsyst_api.database._get("_system")
        for dbname in sys_db.databases():
            if dbname.startswith("mock-database-"):
                print(f"[MOCK] Destroying mock database {dbname}")
                sys_db.delete_database(dbname)


@contextmanager
def authed_request(client: TestClient, username: UsernameStr, password: str):
    response = client.post("/auth/", {"username": username, "password": password})
    token = response.json()["access_token"]
    yield {"headers": {"Authorization": f"Bearer {token}"}}


class mocks:
    class users:
        alice = DBUser(
            _key=ALICE_KEY,
            username="alice",
            password_hash=hash_password(ALICE_PASSWORD),
            joined_at=datetime(2020, 7, 23, 22, 41, 0),
            email_is_confirmed=True,
            email="hey@alice.example.com",
        )

        john = DBUser(
            _key=JOHN_KEY,
            username="john",
            password_hash=hash_password(JOHN_PASSWORD),
            joined_at=datetime(2019, 6, 12, 12, 0, 51),
            email="john@example.com",
        )

    class subjects:
        français = Subject(
            owner_key=ALICE_KEY,
            # object_key=objectbarekey(),
            color="red",
            goal=1.0,
            room="L204",
            weight=3.0,
            name="Français",
        )

        mathematiques = Subject(
            owner_key=ALICE_KEY,
            # object_key=objectbarekey(),
            color="cyan",
            goal=0.4,
            room="L624",
            weight=6,
            name="Mathématiques",
        )

        sciences_de_l_ingénieur = Subject(
            owner_key=JOHN_KEY,
            # object_key=objectbarekey(),
            color="#c0ffee",
            goal=0.8,
            room="",
            weight=48,
            name="Sciences de l'ingénieur",
        )
