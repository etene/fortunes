from http import HTTPStatus
import pytest
from django.test import AsyncClient

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_get_random_fortune_no_fortunes(async_client: AsyncClient):
    response = await async_client.get("/random/")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.content.decode() == "No fortunes"
