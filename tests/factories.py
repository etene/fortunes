from typing import Any
from django.db.models import Model
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory
import pytest_asyncio
import pytest
from datetime import UTC

from fortunes.app.models import Author, Fortune


def get_base_name(factory_class: type[DjangoModelFactory]) -> str:
    return factory_class.__name__.removesuffix("Factory").lower()


class AsyncFactory[FortunesModelT: Model]():

    @classmethod
    def as_fixture(cls, factory_class: type[DjangoModelFactory[FortunesModelT]]):
        base_name = get_base_name(factory_class)

        def _fixture():
            return cls(factory_class)

        return pytest.fixture(name=f"{base_name}_factory")(_fixture)

    def __init__(self, factory_class: type[DjangoModelFactory[FortunesModelT]]) -> None:
        self.factory_class = factory_class

    @property
    def model(self) -> type[FortunesModelT]:
        return self.factory_class._meta.model

    async def _abuild(self, **overrides: Any) -> FortunesModelT:
        instance = self.factory_class.build(**overrides)
        if isinstance(instance, Fortune):
            await instance.author.asave()
        return instance

    async def create(self, **overrides: Any) -> FortunesModelT:
        built = await self._abuild(**overrides)
        await built.asave()
        return built

    __call__ = create

    async def _abuild_batch(self, size: int, **kwargs) -> list[FortunesModelT]:
        return [await self._abuild(**kwargs) for _ in range(size)]

    async def create_batch(self, size: int, **overrides: Any) -> list[FortunesModelT]:
        created = await self._abuild_batch(size=size, **overrides)
        return await self.model.objects.abulk_create(objs=created)  # type: ignore[attr-defined]

    def build_batch(self, size: int, **kwargs: Any) -> list[FortunesModelT]:
        return self.factory_class.build_batch(size=size, **kwargs)


class AuthorFactory(DjangoModelFactory[Author]):
    class Meta:
        model = Author

    id = Faker("random_int")
    name = Faker("first_name")
    birthday = Faker("past_date", tzinfo=UTC)
    immich_id = Faker("uuid4", cast_to=None)


class FortuneFactory(DjangoModelFactory[Fortune]):
    class Meta:
        model = Fortune

    id = Faker("random_int")
    author = SubFactory(AuthorFactory)
    text = Faker("paragraph")
    date = Faker("date_object")
    hidden = False


_author_factory = AsyncFactory.as_fixture(AuthorFactory)
_fortune_factory = AsyncFactory.as_fixture(FortuneFactory)


@pytest_asyncio.fixture
async def author(author_factory: AsyncFactory[Author]) -> Author:
    return await author_factory()


@pytest_asyncio.fixture
async def fortune(
    fortune_factory: AsyncFactory[Fortune], author_factory: AsyncFactory[Author]
) -> Fortune:
    return await fortune_factory()
