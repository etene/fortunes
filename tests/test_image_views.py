from datetime import UTC, datetime, time, timedelta
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


@pytest.mark.parametrize("fortune_has_date", (True, False))
async def test_get_random_image_for_fortune(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
    immich_mock: ImmichClientMock,
    fake_jpeg_image: bytes,
    fortune_has_date: bool,
):
    fortune = await fortune_factory(
        has_date=fortune_has_date, author__has_immich_id=True
    )
    if fortune_has_date:
        assert fortune.date
        fortune_datetime = datetime.combine(fortune.date, time(hour=12), tzinfo=UTC)
        # It's the closest one in date to the fortune
        expected_image = ImmichAssetResponseDtoFactory.create(
            local_date_time=fortune_datetime + timedelta(hours=1)
        )
        immich_mock.random_search_results.extend(
            (
                ImmichAssetResponseDtoFactory.create(
                    local_date_time=fortune_datetime + timedelta(hours=3)
                ),
                expected_image,
                ImmichAssetResponseDtoFactory.create(
                    local_date_time=fortune_datetime - timedelta(hours=2)
                ),
            )
        )
    else:
        immich_mock.random_search_results.extend(
            ImmichAssetResponseDtoFactory.create_batch(3)
        )
        expected_image = immich_mock.random_search_results[0]

    resp = await async_client.get(f"/random_image/{fortune.id}/")
    assert resp.status_code == HTTPStatus.OK
    assert resp.headers["content-type"] == "image/jpg"
    assert resp.content == fake_jpeg_image

    assert immich_mock.download_asset_mock.call_args_list == [
        call(id=expected_image.id)
    ]
