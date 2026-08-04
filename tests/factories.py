from typing import Any, Protocol
from factory.django import DjangoModelFactory
from factory import Faker
import pytest_asyncio


from fortunes.app.models import Author


class FactoryProtocol[FortunesModelT](Protocol):
    async def __call__(self, **overrides: Any) -> FortunesModelT: ...


class AuthorFactory(DjangoModelFactory[Author]):
    class Meta:
        model = Author

    name = Faker("name")
    birthday = Faker("date")
    immich_id = Faker("uuid4")


@pytest_asyncio.fixture
async def author_factory():
    async def _factory(**overrides: Any) -> Author:
        author = AuthorFactory.build(**overrides)
        await author.asave()
        return author

    return _factory


@pytest_asyncio.fixture
async def author(author_factory: FactoryProtocol[Author]) -> Author:
    return await author_factory()
