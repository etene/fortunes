import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Author, Fortune
from tests.factories import AsyncFactory
from tests.tools import HTMLElement, assert_html
from datetime import date

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_get_fortune_edit_form(
    fortune: Fortune,
    author_factory: AsyncFactory[Author],
    async_client: AsyncClient,
):
    author = fortune.author
    other_author = await author_factory()
    response = await async_client.get(f"/{fortune.id}/edit/")
    assert response.status_code == HTTPStatus.OK
    assert_html(
        response.content,
        # There is a form to edit the fortune
        HTMLElement(
            tag="form",
            attrs={
                "method": "post",
                "class": "form",
            },
        ),
        # There is an input to edit the date, with today as default
        HTMLElement(
            tag="input",
            attrs={
                "type": "date",
                "value": str(date.today()),
                "class": "form-control is-valid",
                "placeholder": "Date",
            },
        ),
        # There is a text area to edit the fortune
        HTMLElement(
            tag="textarea",
            content=fortune.text,
            attrs={
                "name": "fortune_text",
                "cols": "40",
                "rows": "10",
                "class": "form-control is-valid",
                "placeholder": "Fortune",
                "id": "id_fortune_text",
            },
        ),
        # There is an input option for each author
        HTMLElement(
            tag="option",
            content=author.name,
            attrs={
                "value": str(author.id),
                "selected": "",
            },
        ),
        HTMLElement(
            tag="option",
            content=other_author.name,
            attrs={
                "value": str(other_author.id),
            },
        ),
        # There is a submit button in the form
        HTMLElement(
            tag="button",
            content="Soumettre",
            attrs={
                "class": "btn btn-primary",
                "type": "submit",
            },
        ),
    )


async def test_edit_fortune_text(
    fortune: Fortune,
    async_client: AsyncClient,
):
    assert fortune.date
    response = await async_client.post(
        f"/{fortune.id}/edit/",
        data={
            "text": "New text.",
            "author_id": fortune.author.id,
            "date": fortune.date.strftime("%Y-%m-%d"),
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == f"/{fortune.id}/"
    await fortune.arefresh_from_db()
    assert fortune.text == "New text."
    assert fortune.date


async def test_edit_fortune_error(
    fortune: Fortune,
    async_client: AsyncClient,
):
    bad_author_id = fortune.author.id + 1
    response = await async_client.post(
        f"/{fortune.id}/edit/",
        data={
            "author_id": bad_author_id,
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert_html(
        response.content,
        HTMLElement(
            tag="div",
            # FIXME: the author name should be in the error, not its ID
            content=f"Sélectionnez un choix valide. {bad_author_id} n'en fait pas partie.",
            attrs={
                "class": "invalid-feedback d-block",
            },
        ),
    )
