from typing import Literal, Optional, Union

from pydantic import PositiveFloat
from pydantic.color import Color
from schoolsyst_api.models import BaseModel, OwnedResource, Primantissa
from slugify import slugify


class InSubject(BaseModel):
    """
    A subject.
    """

    name: str
    color: Color
    weight: Union[PositiveFloat, Literal[0]] = 1.0
    goal: Optional[Primantissa] = None
    location: str = ""

    @property
    def slug(self) -> str:  # unique
        return slugify(self.name)


class PatchSubject(InSubject):
    """
    A special model used for patching subjects.
    """

    name: Optional[str] = None
    color: Optional[Color] = None


class Subject(InSubject, OwnedResource):
    pass
