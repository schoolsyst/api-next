from pydantic import conint
from schoolsyst_api.models import BaseModel


class HomeworkCompletedStats(BaseModel):
    """
    Global statistics for completed homework accross all users of schoolsyst
    """

    week: conint(ge=0)
    month: conint(ge=0)
    year: conint(ge=0)
    all_time: conint(ge=0)
