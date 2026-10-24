from http import HTTPStatus
import re
import pytest
from django.test import AsyncClient

from fortunes.app.models import Author, Fortune
from tests.factories import AsyncFactory
from tests.tools import match_html_elements

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
    )
    assert len(fortune_id_spans) == 3
    assert {i.content_lines[0] for i in fortune_id_spans} == {
        f"\xa0{i.id}" for i in author1_fortunes
    }
