import os
from contextlib import contextmanager
from typing import Optional
from uuid import uuid4

import schoolsyst_api.database
from arango.database import StandardDatabase
from fastapi.testclient import TestClient
from schoolsyst_api.models import UsernameStr


@contextmanager
def database_mock() -> StandardDatabase:
    db_name = f"mock-database-{uuid4()}"
    os.environ["CURRENT_MOCK_DB_NAME"] = db_name
    print(f"[MOCK] Creating mock database {db_name}")
    db: Optional[StandardDatabase] = schoolsyst_api.database.initialize(db_name)
    if db is None:
        raise ValueError("Could not create mock database")
    yield db

    print(f"[MOCK] Destroying mock database {db_name}")
    sys_db = schoolsyst_api.database._get("_system")
    sys_db.delete_database(db_name)


@contextmanager
def authed_request(client: TestClient, username: UsernameStr, password: str):
    response = client.post("/auth/", {"username": username, "password": password})
    token = response.json()["access_token"]
    yield {"headers": {"Authorization": f"Bearer {token}"}}
