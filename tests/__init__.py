import os
from contextlib import contextmanager
from typing import List, Optional

import nanoid
import schoolsyst_api.database
import tests.mocks
from arango.database import StandardDatabase
from fastapi.testclient import TestClient
from schoolsyst_api.accounts.models import UsernameStr
from schoolsyst_api.main import api
from schoolsyst_api.models import BaseModel

os.environ["TESTING"] = "True"
client = TestClient(api)


@contextmanager
def database_mock() -> StandardDatabase:
    os.environ["TESTING"] = "True"
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


def insert_mocks(
    db: StandardDatabase, collection_name: str,
):
    mock_objects: List[BaseModel] = [
        getattr(getattr(tests.mocks, collection_name), m)
        for m in dir(getattr(tests.mocks, collection_name))
        if not m.startswith("__")
    ]
    for mock in mock_objects:
        db.collection(collection_name).insert(mock.json(by_alias=True))
