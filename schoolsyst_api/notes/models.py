from enum import auto
from typing import Optional

import requests
from fastapi_utils.enums import StrEnum
from pydantic import HttpUrl
from schoolsyst_api.models import OwnedResource


class NoteContentType(StrEnum):
    """
    A note's content type, if created with schoolsyst,
    or the value "external" if imported from an external source.
    """

    html = auto()
    markdown = auto()
    asciidoc = auto()
    external = auto()


class NoteExportContentType(StrEnum):
    """
    The content types that a note can be exported to.
    """

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
    """
    A service for an externally-sourced note.
    """

    pass


class Note(OwnedResource):
    """
    A note, can be a lesson, an exercise, or anything made of text.
    Could be analyzed for automatic quizz generation in the future.
    """

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
