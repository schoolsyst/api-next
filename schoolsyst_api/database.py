import os
from typing import Optional

import arango.database
from arango import ArangoClient
from dotenv import load_dotenv

# Different collections stored in the 'schoolsyst' standard database
COLLECTIONS = [
    "subjects",
    "users",
    "settings",
    "subjects",
    "quizzes",
    "notes",
    "grades",
    "homework",
    "events",
    "event_mutations",
    "password_reset_requests",
    "email_confirmations",
]


def create_collection_if_missing(
    database: arango.database.StandardDatabase, collection_name: str
):
    if not database.has_collection(collection_name):
        database.create_collection(collection_name)


def create_indexes(
    db: arango.database.StandardDatabase,
) -> arango.database.StandardDatabase:
    # Users
    db.collection("users").add_persistent_index(fields=["emails", "username"])
    return db


def _get_default_name():
    if os.getenv("TESTING"):
        return os.getenv("CURRENT_MOCK_DB_NAME")
    else:
        return "schoolsyst"


def initialize(database_name: Optional[str] = None) -> arango.database.StandardDatabase:
    load_dotenv(".env")
    database_name = database_name or _get_default_name()

    print(f"[ DB ] Initializing database {database_name}")

    sys_db = _get("_system")

    if not sys_db.has_database(database_name):
        sys_db.create_database(database_name)

    db = _get(database_name)

    for c in COLLECTIONS:
        create_collection_if_missing(db, c)

    db = create_indexes(db)

    return db


# if we use this directly in Depends(...)
# FastAPI will believe database_name is a query parameter.
def _get(database_name: Optional[str] = None) -> arango.database.StandardDatabase:
    database_name = database_name or _get_default_name()
    print(f"[ DB ] Logging into database {database_name}")

    client = ArangoClient(hosts=os.getenv("ARANGODB_HOST", "http://localhost:8529"))
    username, password = os.getenv("ARANGODB_USERNAME"), os.getenv("ARANGODB_PASSWORD")
    db = client.db(
        name=database_name, username=username, password=password, verify=True
    )

    return db


def get() -> arango.database.StandardDatabase:
    return _get(_get_default_name())
