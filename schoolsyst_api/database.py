import os

import arango.database
from arango import ArangoClient
from dotenv import load_dotenv


def initialize() -> arango.database.StandardDatabase:
    load_dotenv(".env")
    client = ArangoClient(hosts=os.getenv("ARANGO_HOST", "http://localhost:8529"))
    db = client.db(
        os.getenv("ARANGO_DB_NAME", "schoolsyst"),
        username=os.getenv("ARANGO_USERNAME"),
        password=os.getenv("ARANGO_PASSWORD"),
    )
    if not db.has_database("schoolsyst"):
        db.create_database("schoolsyst")

    return db
