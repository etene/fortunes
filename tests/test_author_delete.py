from django.contrib import messages
from django.contrib.messages import get_messages
import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Author
from django.contrib.messages.storage.base import Message

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_delete_author(
    author: Author,
    async_client: AsyncClient,
):
    response = await async_client.post(f"/author/{author.id}/delete/")
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers["Location"] == "/"

    with pytest.raises(Author.DoesNotExist):
        await author.arefresh_from_db()

    response_messages = list(get_messages(response.asgi_request))
    assert response_messages == [
        Message(
            level=messages.SUCCESS,
            message="L'auteur a été supprimé",
            extra_tags="success",
        )
    ]
