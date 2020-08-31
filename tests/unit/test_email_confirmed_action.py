from datetime import timedelta
from pathlib import Path

from schoolsyst_api.email_confirmed_action import EmailConfirmedAction
from tests import mocks

MOCKS_MAIL_TEMPLATES_DIR = (
    Path(__file__).parent.parent / "mocks" / "email_templates" / "dist"
)

eca = EmailConfirmedAction(
    name="lorem",
    callback_url="ipsum://{}",
    token_valid_for=timedelta(1),
    email_subject="Ut id ea voluptate enim laborum.",
)
eca._templates_directory = MOCKS_MAIL_TEMPLATES_DIR


def test_jwt_sub_format():
    assert eca.jwt_sub_format == "lorem:{}"


def test_template_pseudo_filepath():
    assert eca.template_pseudo_filepath == MOCKS_MAIL_TEMPLATES_DIR / "lorem"


def test_template_filepath():
    assert eca.template_filepath("html") == MOCKS_MAIL_TEMPLATES_DIR / "lorem.html"
    assert eca.template_filepath("txt") == MOCKS_MAIL_TEMPLATES_DIR / "lorem.txt"


def test_send_mail_function():
    assert callable(eca._send_mail_function)


def test_action_url():
    assert eca._action_url("hmmm") == "ipsum://hmmm"


def test_render_mail_template():
    assert (
        eca._render_mail_template(
            template="""\
<h1>Hello, {{username}}.</h1>
Please click on <a href="{{url}}">here</a>
<small>Token: <code>{{token}}</code></small>
Sent to <a href="mailto:{{email}}">your email</a>
""",
            current_user=mocks.users.alice,
            token="hmmm",
        )
        == f"""\
<h1>Hello, {mocks.users.alice.username}.</h1>
Please click on <a href="ipsum://hmmm">here</a>
<small>Token: <code>hmmm</code></small>
Sent to <a href="mailto:{mocks.users.alice.email}">your email</a>
"""
    )


def test_render_mail_template_file():
    assert (
        eca._render_mail_template_file(
            "html", token="hmmm", current_user=mocks.users.alice
        )
        == f"""\
<h1>Hello, {mocks.users.alice.username}.</h1>
Please click on <a href="ipsum://hmmm">here</a>
<small>Token: <code>hmmm</code></small>
Sent to <a href="mailto:{mocks.users.alice.email}">your email</a>
"""
    )
    assert (
        eca._render_mail_template_file(
            "txt", token="hmmm", current_user=mocks.users.alice
        )
        == f"""\
Hello, {mocks.users.alice.username}.

Please click here: ipsum://hmmm Token: hmmm Sent to your email: {mocks.users.alice.email}
"""
    )
