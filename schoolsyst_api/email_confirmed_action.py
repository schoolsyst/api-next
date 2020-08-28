from datetime import timedelta
from pathlib import Path
from typing import Callable, Literal, Union

import chevron
from fastapi import BackgroundTasks, HTTPException, status
from schoolsyst_api.accounts import create_jwt_token, verify_jwt_token
from schoolsyst_api.accounts.models import User


class EmailConfirmedAction:
    name: str
    callback_url: str
    token_valid_for: timedelta

    def __init__(
        self, name: str, callback_url: str, token_valid_for: timedelta,
    ) -> None:
        """
        `callback_url` is used as the link to click on in the email.
        All occurences of `{}` will be replaced with the generated token.
        """
        self.name = name
        self.callback_url = callback_url
        self.token_valid_for = token_valid_for

    @property
    def jwt_sub_format(self) -> str:
        return f"{self.name}:{{}}"

    @property
    def mail_template_path(self) -> str:
        """
        The mail template (.html compiled from .mjml file)'s path,
        assuming the project root as the current directory.
        The extension still needs to be added to get either the HTML version (.html)
        or the plain-text one (.txt)
        """
        return str(Path("static") / "mail_templates" / "dist" / self.name)

    @property
    def _send_mail_function(self) -> Callable[[str], bool]:
        def send_mail(token: str):
            pass

        return send_mail

    def _action_url(self, token: str) -> str:
        return self.callback_url.format(token)

    def _render_mail_template(
        self,
        token: str,
        fmt: Union[Literal["html"], Literal["txt"]],
        current_user: User,
    ) -> str:
        """
        Renders the mail template (at `self.mail_template_path()`)
        and returns the HTML/plaintext string
        """
        return chevron.render(
            Path(f"{self.mail_template_path}.{fmt}").read_text(),
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

        tasks.add_task(self._send_mail_function, token)

    def handle_token_verification(self, input_token: str, current_user: User):
        if not verify_jwt_token(
            input_token, self.jwt_sub_format, current_user.username
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="The token is either corrupted, emitted by another user or expired",
            )
