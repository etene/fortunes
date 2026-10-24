from django.contrib import messages
import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Author, Fortune

from tests.factories import AsyncFactory
from tests.tools import assert_message

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

    assert_message(
        response,
        level=messages.SUCCESS,
        message=f"L'auteur {author.name!r} a été supprimé",
    )


async def test_delete_author_with_fortunes(
    author: Author,
    async_client: AsyncClient,
    fortune_factory: AsyncFactory[Fortune],
):
    await fortune_factory(author=author)
    response = await async_client.post(f"/author/{author.id}/delete/")
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers["Location"] == "/"
    assert_message(
        response,
        level=messages.ERROR,
        message=f"Impossible de supprimer {author.name}, qui a encore des citations.",
    )


async def test_delete_author_not_found(
    author: Author,
    async_client: AsyncClient,
):
    author_id = author.id
    await author.adelete()
    response = await async_client.post(f"/author/{author_id}/delete/")
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers["Location"] == "/"

    assert_message(
        response,
        level=messages.ERROR,
        message="Aucun auteur correspondant trouvé",
    )
