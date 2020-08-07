from fastapi.routing import APIRouter

# Shortcuts
from schoolsyst_api.accounts.users import (  # noqa
    get_current_confirmed_user,
    get_current_user,
)

router = APIRouter()
