from unittest.mock import AsyncMock
from uuid import UUID
from immichpy.client.generated.api.people_api import PeopleApi
from immichpy.client.generated.models.asset_response_dto import AssetResponseDto
from immichpy.client.generated.models.random_search_dto import RandomSearchDto
from immichpy.client.wrapper.assets_api_wrapped import AssetsApiWrapped
import pytest
from pathlib import Path

from immichpy.client.generated.models.person_response_dto import PersonResponseDto


class ImmichClientMock:

    def __init__(self) -> None:
        self.persons: list[PersonResponseDto] = []
        self.random_search_results: list[AssetResponseDto] = []
        self.search_person_mock = AsyncMock(side_effect=self._search_persons_callback)
        self.download_asset_mock = AsyncMock(side_effect=self._download_asset_callback)
        self.search_random_mock = AsyncMock(side_effect=self._search_random_callback)
        self.get_person_thumbnail_mock = AsyncMock(
            side_effect=self._get_person_thumbnail_callback
        )
        self.image: bytes | None = None

    async def _search_persons_callback(self, name: str) -> list[PersonResponseDto]:
        return [i for i in self.persons if i.name == name]

    def register(self, monkeypatch: pytest.MonkeyPatch):
        from immichpy.client.generated.api.search_api import SearchApi

        monkeypatch.setattr(SearchApi, "search_person", self.search_person_mock)
        monkeypatch.setattr(SearchApi, "search_random", self.search_random_mock)
        monkeypatch.setattr(
            PeopleApi, "get_person_thumbnail", self.get_person_thumbnail_mock
        )
        monkeypatch.setattr(
            AssetsApiWrapped, "download_asset", self.download_asset_mock
        )

    async def _search_random_callback(
        self, random_search_dto: RandomSearchDto
    ) -> list[AssetResponseDto]:
        return self.random_search_results

    async def _download_asset_callback(self, id: UUID) -> bytes:
        assert self.image
        return self.image

    async def _get_person_thumbnail_callback(self, id: UUID) -> bytes:
        assert self.image
        return self.image


@pytest.fixture
def immich_mock(
    monkeypatch: pytest.MonkeyPatch, fake_jpeg_image: bytes
) -> ImmichClientMock:
    m = ImmichClientMock()
    m.image = fake_jpeg_image
    m.register(monkeypatch)
    return m


@pytest.fixture(name="fake_jpeg_image", scope="session")
def _fake_jpeg_image(test_data_dir: Path) -> bytes:
    return test_data_dir.joinpath("1px.jpeg").read_bytes()
