from http import HTTPStatus
from unittest.mock import call
import pytest
from django.test import AsyncClient
from fortunes.app.models import Author, Fortune
from tests.factories import AsyncFactory, ImmichAssetResponseDtoFactory
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
        call(id=author.immich_id)
    ]


async def test_get_author_thumbnail_no_immich_id(
    author_factory: AsyncFactory[Author],
    async_client: AsyncClient,
):

    author = await author_factory(has_immich_id=False)
    resp = await async_client.get(f"/author/{author.id}/thumbnail/")
    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.content.decode() == f"{author.name} has no immich id"


async def test_get_random_image_for_fortune(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
    immich_mock: ImmichClientMock,
    fake_jpeg_image: bytes,
):
    fortune = await fortune_factory(has_date=True, author__has_immich_id=True)
    asset_responses = ImmichAssetResponseDtoFactory.create_batch(3)
    immich_mock.random_search_results.extend(asset_responses)
    resp = await async_client.get(f"/random_image/{fortune.id}/")
    assert resp.status_code == HTTPStatus.OK
    assert resp.headers["content-type"] == "image/jpg"
    assert resp.content == fake_jpeg_image

    # The first "random" search result has been downloaded
    assert immich_mock.download_asset_mock.call_args_list == [
        call(id=asset_responses[0].id)
    ]
