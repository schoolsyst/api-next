import os
from contextlib import contextmanager
from uuid import uuid4

import schoolsyst_api.database
from arango.database import StandardDatabase


@contextmanager
def database_mock() -> StandardDatabase:
    db_name = f"mock-database-{uuid4()}"
    os.environ["CURRENT_MOCK_DB_NAME"] = db_name
    print(f"[MOCK] Creating mock database {db_name}")
    yield schoolsyst_api.database.initialize(db_name)

    print(f"[MOCK] Destroying mock database {db_name}")
    sys_db = schoolsyst_api.database.get("_system")
    sys_db.delete_database(db_name)
