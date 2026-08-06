from typing import Any, Protocol
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory
import pytest_asyncio


from fortunes.app.models import Author, Fortune


class FactoryProtocol[FortunesModelT](Protocol):
    async def __call__(self, **overrides: Any) -> FortunesModelT: ...


class AuthorFactory(DjangoModelFactory[Author]):
    class Meta:
        model = Author

    name = Faker("first_name")
    birthday = Faker("date")
    immich_id = Faker("uuid4")


class FortuneFactory(DjangoModelFactory[Fortune]):
    class Meta:
        model = Fortune

    author = SubFactory(AuthorFactory)
    text = Faker("paragraph")
    date = Faker("date")
    hidden = False


@pytest_asyncio.fixture
async def author_factory():
    async def _factory(**overrides: Any) -> Author:
        author = AuthorFactory.build(**overrides)
        await author.asave()
        return author

    return _factory


@pytest_asyncio.fixture
async def fortune_factory():
    async def _factory(**overrides: Any) -> Fortune:
        fortune = FortuneFactory.build(**overrides)
        await fortune.author.asave()
        await fortune.asave()
        return fortune

    return _factory


@pytest_asyncio.fixture
async def fortune(fortune_factory: FactoryProtocol[Fortune]):
    return await fortune_factory()


@pytest_asyncio.fixture
async def author(author_factory: FactoryProtocol[Author]) -> Author:
    return await author_factory()
