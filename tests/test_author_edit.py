from http import HTTPStatus
from django.contrib import messages
import pytest
from fortunes.app.models import Author
from django.test import AsyncClient

from tests.tools import assert_message

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_edit_author_no_changes(
    author: Author,
    async_client: AsyncClient,
):
    assert author.birthday
    response = await async_client.post(
        f"/author/{author.id}/edit",
        data={
            "name": author.name,
            "birthday": author.birthday.strftime("%Y-%m-%d"),
            "immich_id": author.immich_id,
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    assert_message(
        response,
        level=messages.INFO,
        message="Aucune modification",
    )
    updated_author = await Author.objects.aget(id=author.id)
    assert updated_author.name == author.name
    assert updated_author.birthday == author.birthday
    assert updated_author.immich_id == author.immich_id
