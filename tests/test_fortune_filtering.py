from http import HTTPStatus
import re
from django.contrib import messages
import pytest
from django.test import AsyncClient

from fortunes.app.models import Author, Fortune
from tests.factories import AsyncFactory
from tests.tools import assert_message, match_html_elements

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_filter_fortunes_by_author(
    fortune_factory: AsyncFactory[Fortune],
    author_factory: AsyncFactory[Author],
    async_client: AsyncClient,
):
    author1, author2 = await author_factory.create_batch(2)
    author1_fortunes = await fortune_factory.create_batch(3, author=author1)
    await fortune_factory(author=author2)
    response = await async_client.get(
        "/browse/", query_params={"author_id": author1.id}
    )
    assert response.status_code == HTTPStatus.OK

    fortune_id_spans = match_html_elements(
        response.content,
        tag="span",
        attrs={"class": "font-monospace"},
        contains=re.compile(r"^.*\d+$"),
        expected_matches=3,
    )
    assert {i.content_lines[0] for i in fortune_id_spans} == {
        f"\xa0{i.id}" for i in author1_fortunes
    }
    assert_message(
        response,
        message="3 citations trouvées",
        level=messages.SUCCESS,
    )


async def test_search_fortune_text(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
):
    fortune = await fortune_factory(text="un guéopard")
    other_fortune = await fortune_factory()
    response = await async_client.get("/browse/", query_params={"text": "guéopar"})
    assert response.status_code == HTTPStatus.OK
    html = response.content.decode()
    assert other_fortune.text not in html
    assert fortune.text in html


async def test_search_fortunes_by_date(
    fortune_factory: AsyncFactory[Fortune],
):
    pass
