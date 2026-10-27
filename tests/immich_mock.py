from unittest.mock import AsyncMock
import pytest

from immichpy.client.generated.models.person_response_dto import PersonResponseDto


class ImmichClientMock:

    def __init__(self) -> None:
        self.persons: list[PersonResponseDto] = []
        self.search_person_mock = AsyncMock(side_effect=self._search_persons_callback)

    async def _search_persons_callback(self, name: str) -> list[PersonResponseDto]:
        return [i for i in self.persons if i.name == name]

    def register(self, monkeypatch: pytest.MonkeyPatch):
        from immichpy.client.generated.api.search_api import SearchApi

        monkeypatch.setattr(SearchApi, "search_person", self.search_person_mock)


@pytest.fixture
def immich_mock(monkeypatch: pytest.MonkeyPatch) -> ImmichClientMock:
    m = ImmichClientMock()
    m.register(monkeypatch)
    return m
