import os

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


def initialize() -> arango.database.StandardDatabase:
    load_dotenv(".env")
    print("[PERF] Initializing database")
    sys_db = get()

    if not sys_db.has_database(os.getenv("ARANGO_DB_NAME")):
        sys_db.create_database(os.getenv("ARANGO_DB_NAME"))

    for c in COLLECTIONS:
        create_collection_if_missing(sys_db, c)

    sys_db = create_indexes(sys_db)

    return sys_db


def get() -> arango.database.StandardDatabase:
    print("[PERF] Logging into the database")
    client = ArangoClient(hosts=os.getenv("ARANGO_HOST", "http://localhost:8529"))
    username, password = os.getenv("ARANGO_USERNAME"), os.getenv("ARANGO_PASSWORD")
    sys_db = client.db(
        name="_system", username=username, password=password, verify=True
    )

    return sys_db
