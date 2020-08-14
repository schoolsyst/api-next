from hashlib import sha256
from typing import Callable

from fastapi.requests import Request
from fastapi_etag import Etag
from schoolsyst_api import database
from schoolsyst_api.models import OBJECT_KEY_FORMAT


def compute_for(collection_name: str) -> Callable[[Request], str]:
    """
    Returns an `Etag` with a function that takes a Request and returns a SHA256
    hexdigest hash of the `updated_at` field of an object from `collection_name`
    with a _key equal to a path parameter `{key}`'s value as the etag generation function.
    """

    async def compute(request: Request) -> str:
        # Get the database
        db = database.get()
        # Get the key of the object from the path parameters from Request
        key = request.path_params["key"]
        # Get the collection name from the request path
        collection_name = request.path.split("/")[1].replace("-", "_")
        # Get the full key by getting the current user
        # current_user_key = parse(auth.JWT_SUB_FORMAT, request.auth)
        full_key = OBJECT_KEY_FORMAT.format(object=key, owner="current_user.key")
        # Get the document from collection collection_name with _key key
        document = db.collection(collection_name).get(full_key)
        # Get the updated_at date
        updated_at = document["updated_at"]
        # Compute a hash of thet updated_at date
        sha256hash = sha256(updated_at)
        # Get the hexdigest of that hash (which is a `str`)
        hexdigest = sha256hash.hexdigest()
        return hexdigest

    return Etag(compute)
