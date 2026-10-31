import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Author, Fortune
from tests.factories import AsyncFactory
from tests.tools import match_html_elements

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


@pytest.mark.parametrize("fortune_has_date", (True, False))
async def test_get_fortune_edit_form(
    fortune_factory: AsyncFactory[Fortune],
    author_factory: AsyncFactory[Author],
    async_client: AsyncClient,
    fortune_has_date: bool,
):
    author, other_author = await author_factory.create_batch(2)
    fortune = await fortune_factory(author=author, has_date=fortune_has_date)
    response = await async_client.get(f"/{fortune.id}/edit/")
    assert response.status_code == HTTPStatus.OK
    assert (
        len(
            match_html_elements(
                response.content,
                # There is a form to edit the fortune
                tag="form",
                attrs={
                    "method": "post",
                    "class": "form",
                },
            )
        )
        == 1
    )
    date_form_input = match_html_elements(
        response.content,
        # There is an input to edit the date
        tag="input",
        attrs={
            "type": "date",
            "name": "date",
            "class": "form-control is-valid",
            "placeholder": "Date",
        },
        expected_matches=1,
    )[0]
    if fortune_has_date:
        assert date_form_input.attrs["value"] == str(fortune.date)
    match_html_elements(
        response.content,
        tag="textarea",
        contains=fortune.text,
        attrs={
            "name": "text",
            "cols": "40",
            "rows": "10",
            "class": "form-control is-valid",
            "placeholder": "Fortune",
            "id": "id_text",
        },
        expected_matches=1,
    )

    match_html_elements(
        response.content,
        # There is an input option for each author
        tag="option",
        contains=author.name,
        attrs={
            "value": str(author.id),
            "selected": None,
        },
        expected_matches=1,
    )
    match_html_elements(
        response.content,
        tag="option",
        contains=other_author.name,
        attrs={
            "value": str(other_author.id),
        },
        expected_matches=1,
    )
    match_html_elements(
        response.content,
        # There is a submit button in the form
        tag="button",
        contains="Soumettre",
        attrs={
            "class": "btn btn-primary",
            "type": "submit",
        },
        expected_matches=1,
    )


async def test_edit_fortune_text(
    fortune: Fortune,
    async_client: AsyncClient,
):
    old_date = fortune.date
    response = await async_client.post(
        f"/{fortune.id}/edit/",
        data={
            "text": "New text.",
            "author_id": fortune.author.id,
            "date": fortune.date.strftime("%Y-%m-%d") if fortune.date else "",
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == f"/{fortune.id}/"
    await fortune.arefresh_from_db()
    assert fortune.text == "New text."
    assert fortune.date == old_date


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

    match_html_elements(
        html=response.content,
        tag="div",
        # FIXME: the author name should be in the error, not its ID
        contains=f"Sélectionnez un choix valide. {bad_author_id} n’en fait pas partie.",
        attrs={
            "class": "invalid-feedback d-block",
        },
        expected_matches=1,
    )
