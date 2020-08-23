from enum import auto

from fastapi_utils.enums import StrEnum
from schoolsyst_api.models import OwnedResource


class NoteType(StrEnum):
    html = auto()
    markdown = auto()
    asciidoc = auto()
    external = auto()


class NoteContentType(StrEnum):
    pdf = auto()
    tex = auto()
    docx = auto()
    txt = auto()
    odt = auto()
    markdown = auto()
    asciidoc = auto()
    rst = auto()
    epub = auto()
    mediawiki = auto()


class Note(OwnedResource):
    name: str = ""
    content: str = ""
    type: NoteType = NoteType.html
    # quizzes: List[Quiz] = []

    @property
    def thumbnail_url(self) -> str:
        return f"/notes/{self._key}/thubmnail"
