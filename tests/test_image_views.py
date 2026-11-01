from http import HTTPStatus
from unittest.mock import call
import pytest
from django.test import AsyncClient
from fortunes.app.models import Author
from tests.factories import AsyncFactory
from tests.immich_mock import ImmichClientMock

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_get_author_thumbnail(
    author_factory: AsyncFactory[Author],
    async_client: AsyncClient,
    immich_mock: ImmichClientMock,
    fake_jpeg_image: bytes,
):
    author = await author_factory(has_immich_id=True)
    resp = await async_client.get(f"/author/{author.id}/thumbnail/")
    assert resp.status_code == HTTPStatus.OK
    assert resp.headers["content-type"] == "image/jpg"
    assert resp.content == fake_jpeg_image
    assert immich_mock.get_person_thumbnail_mock.call_args_list == [
        call(id=author.immich_id),
    ]
