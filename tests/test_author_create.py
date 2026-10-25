from http import HTTPStatus
import pytest
from uuid import uuid4
from django.test import AsyncClient
from fortunes.app.models import Author

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_create_author_with_immich_id(
    async_client: AsyncClient,
):
    fake_immich_id = uuid4()
    response = await async_client.post(
        path="/author/new/",
        data={
            "name": "Jean-Michel",
            "immich_id": fake_immich_id,
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    created_author = await Author.objects.aget(name="Jean-Michel")
    assert created_author.immich_id == fake_immich_id
    assert response.headers["location"] == f"/author/{created_author.id}/edit/"
