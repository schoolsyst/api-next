from datetime import timedelta
from os import getenv
from pathlib import Path
from typing import Callable, Literal, Union

import chevron
import yagmail
from fastapi import BackgroundTasks, HTTPException, status
from schoolsyst_api.accounts import create_jwt_token, verify_jwt_token
from schoolsyst_api.accounts.models import User


class EmailConfirmedAction:
    name: str
    callback_url: str
    token_valid_for: timedelta
    email_subject: str

    def __init__(
        self,
        name: str,
        callback_url: str,
        token_valid_for: timedelta,
        email_subject: str,
    ) -> None:
        """
        `callback_url` is used as the link to click on in the email.
        All occurences of `{}` will be replaced with the generated token.
        """
        self.name = name
        self.callback_url = callback_url
        self.token_valid_for = token_valid_for
        self.email_subject = email_subject
        self._templates_directory = (
            Path(__file__).parent.parent / "static" / "email_templates" / "dist"
        )

    @property
    def jwt_sub_format(self) -> str:
        return f"{self.name}:{{}}"

    @property
    def template_pseudo_filepath(self) -> Path:
        """
        The mail template (.html compiled from .mjml file)'s path,
        assuming the project root as the current directory.
        The extension still needs to be added to get either the HTML version (.html)
        or the plain-text one (.txt)
        """
        return Path(self._templates_directory) / self.name

    def template_filepath(self, fmt: Union[Literal["html"], Literal["txt"]]) -> Path:
        return Path(f"{self.template_pseudo_filepath}.{fmt}")

    @property
    def _send_mail_function(self) -> Callable[[str, User], None]:
        def send_mail(token: str, current_user: User):
            yagmail.SMTP(getenv("GMAIL_USERNAME"), getenv("GMAIL_PASSWORD")).send(
                to=current_user.email,
                subject=self.email_subject.format(username=current_user.username),
                contents=[
                    self._render_mail_template_file(
                        "html", current_user=current_user, token=token
                    ),
                    self._render_mail_template_file(
                        "txt", current_user=current_user, token=token
                    ),
                ],
            )

        return send_mail

    def _action_url(self, token: str) -> str:
        return self.callback_url.format(token)

    def _render_mail_template_file(
        self,
        fmt: Union[Literal["html"], Literal["txt"]],
        token: str,
        current_user: User,
    ) -> str:
        """
        Renders the mail template (at `self.mail_template_path()`)
        and returns the HTML/plaintext string
        """
        return self._render_mail_template(
            template=Path(self.template_filepath(fmt)).read_text(),
            token=token,
            current_user=current_user,
        )

    def _render_mail_template(
        self, template: str, token: str, current_user: User
    ) -> str:
        """
        Renders the mail template given and returns the rendered string
        """
        return chevron.render(
            template,
            {
                "url": self._action_url(token),
                "token": token,
                "username": current_user.username,
                "email": current_user.email,
            },
        )

    def send_request(self, current_user: User, tasks: BackgroundTasks) -> None:
        token = create_jwt_token(
            self.jwt_sub_format, current_user.username, self.token_valid_for
        )
        tasks.add_task(self._send_mail_function, token, current_user)

    def handle_token_verification(self, input_token: str, current_user: User):
        if not verify_jwt_token(
            input_token, self.jwt_sub_format, current_user.username
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="The token is either corrupted, emitted by another user or expired",
            )
