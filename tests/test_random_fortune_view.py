from http import HTTPStatus
import pytest
from django.test import AsyncClient

from fortunes.app.models import Author, Fortune
from tests.factories import AsyncFactory

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_get_random_fortune_no_fortunes(async_client: AsyncClient):
    response = await async_client.get("/random/")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.content.decode() == "No fortunes"


async def test_get_random_fortune(
    async_client: AsyncClient,
    author: Author,
    fortune_factory: AsyncFactory[Fortune],
):
    expected_quotes = {
        i.text for i in await fortune_factory.create_batch(4, author=author)
    }
    response = await async_client.get("/random/")
    assert response.status_code == HTTPStatus.OK
    assert any(i in response.content.decode() for i in expected_quotes)
