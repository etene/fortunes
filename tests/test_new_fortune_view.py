import pytest
from django.test import AsyncClient
from datetime import date
from http import HTTPStatus

from fortunes.app.models import Author, Fortune

pytestmark = [pytest.mark.django_db, pytest.mark.asyncio]


async def test_create_fortune(
    async_client: AsyncClient,
    author: Author,
):
    response = await async_client.post(
        "/new/",
        data={
            "fortune_author_id": author.id,
            "fortune_text": "test",
            "fortune_date": "20/07/2026",
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    created_fortune = await Fortune.objects.with_authors().aget()
    assert created_fortune.text == "test"
    assert created_fortune.date == date(year=2026, month=7, day=20)
    assert created_fortune.author == author
    assert response.headers["Location"] == f"/{created_fortune.id}/"
