from http import HTTPStatus
from django.contrib import messages
from django.contrib.messages.storage.base import Message
import pytest
from fortunes.app.models import Author
from django.test import AsyncClient
from django.contrib.messages import get_messages

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
    response_messages = list(get_messages(response.asgi_request))
    assert response_messages == [
        Message(
            level=messages.INFO,
            message="Aucune modification",
            extra_tags="info",
        ),
    ]
    updated_author = await Author.objects.aget(id=author.id)
    assert updated_author.name == author.name
    assert updated_author.birthday == author.birthday
    assert updated_author.immich_id == author.immich_id
