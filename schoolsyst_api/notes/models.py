from enum import auto
from typing import Optional

import requests
from fastapi_utils.enums import StrEnum
from pydantic import HttpUrl
from schoolsyst_api.models import OwnedResource


class NoteContentType(StrEnum):
    html = auto()
    markdown = auto()
    asciidoc = auto()
    external = auto()


class NoteExportContentType(StrEnum):
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


class NoteSourceService(StrEnum):
    pass


class Note(OwnedResource):
    name: str = ""
    content: str = ""
    content_type: NoteContentType = NoteContentType.html
    source_url: Optional[HttpUrl]
    # quizzes: List[Quiz] = []

    @property
    def thumbnail_url(self) -> str:
        if not self.source_url:
            return f"/notes/{self._key}/thubmnail"

        raise NotImplementedError()

    @property
    def is_source_down(self) -> bool:
        return self.source_url is not None and requests.get(self.source_url).ok

    @property
    def source_service(self) -> NoteSourceService:
        raise NotImplementedError()
