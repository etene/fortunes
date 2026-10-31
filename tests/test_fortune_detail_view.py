import re
import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Fortune
from tests.factories import AsyncFactory
from tests.tools import match_html_elements

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


@pytest.mark.parametrize("author_has_birthday", (True, False))
@pytest.mark.parametrize("author_has_immich_id", (True, False))
@pytest.mark.parametrize("fortune_has_date", (True, False))
async def test_get_fortune(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
    author_has_birthday: bool,
    author_has_immich_id: bool,
    fortune_has_date: bool,
):
    fortune = await fortune_factory(
        has_date=fortune_has_date,
        author__has_birthday=author_has_birthday,
        author__has_immich_id=author_has_immich_id,
    )
    response = await async_client.get(f"/{fortune.id}/")
    assert response.status_code == HTTPStatus.OK

    # There is a blockquote with the text
    match_html_elements(
        response.content,
        tag="blockquote",
        attrs={"class": "blockquote"},
        contains=fortune.text,
        expected_matches=1,
    )

    # There is an image at the bottom if the author is in immich
    match_html_elements(
        response.content,
        tag="img",
        attrs={
            "src": f"/random_image/{fortune.id}/",
            "class": "card-img-bottom",
        },
        expected_matches=1 if author_has_immich_id else 0,
    )

    # There is a "profile picture" for the author if in immich
    match_html_elements(
        response.content,
        tag="img",
        attrs={
            "class": "rounded float-start",
            "src": f"/author/{fortune.author.id}/thumbnail/",
            "title": f"Photo de {fortune.author.name}",
        },
        expected_matches=1 if author_has_immich_id else 0,
    )

    # The fortune date is written in its header, when it has one
    match_html_elements(
        response.content,
        tag="i",
        attrs={"class": "bi bi-calendar-event"},
        expected_matches=1 if fortune_has_date else 0,
    )

    # The fortune has the author's name and age when saying it (if it has a date, an he has a birthday)
    fortune_subext = re.compile(f"^{fortune.author.name}$")
    if fortune_has_date and author_has_birthday:
        assert fortune.author_age is not None
        fortune_subext = re.compile(f"^{fortune.author.name}, {fortune.author_age}$")
    match_html_elements(
        response.content,
        tag="span",
        attrs={"class": "fst-italic"},
        contains=fortune_subext,
    )
