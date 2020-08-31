from arango.database import StandardDatabase
from fastapi import Depends, Response, status
from fastapi_utils.inferring_router import InferringRouter
from pyzip import PyZip
from schoolsyst_api import database
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.database import COLLECTIONS
from schoolsyst_api.personal_archive.models import PersonalArchive

router = InferringRouter()


@router.get(
    "/personal_data_archive",
    status_code=status.HTTP_201_CREATED,
    description=f"""\
Get an archive of all the data owned by the user.
The response is a zip file containing a JSON response, which is
an object associating keys {', '.join(COLLECTIONS)}
to lists of the corresponding objects.""",
)
async def get_personal_data_archive(
    filename: str = "schoolsyst_data_archive.zip",
    user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
):
    """
    Get an archive of all of the data linked to the user.
    """
    data = {}
    # The user's data
    data["users"] = [db.collection("users").get(user.key)]
    # the data of which the user is the owner for every collection
    for c in COLLECTIONS:
        if c == "users":
            continue
        data[c] = [batch for batch in db.collection(c).find({"owner_key": user.key})]
    # zip the data
    zip_file = PyZip()
    zip_file["data.json"] = PersonalArchive(**data).json(by_alias=True).encode("utf-8")
    return Response(
        content=zip_file.to_bytes(),
        status_code=status.HTTP_201_CREATED,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
        media_type="application/zip",
    )
