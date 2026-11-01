from typing import Any
from uuid import uuid4
from django.db.models import Model
from factory.declarations import SelfAttribute
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, Factory, lazy_attribute, Maybe
from immichpy.client.generated.models.asset_response_dto import AssetResponseDto
from immichpy.client.generated.models.asset_type_enum import AssetTypeEnum
from immichpy.client.generated.models.asset_visibility import AssetVisibility
from immichpy.client.generated.models.person_response_dto import PersonResponseDto
import pytest_asyncio
import pytest

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
    birthday = Maybe(
        decider="has_birthday",
        yes_declaration=Faker("date_of_birth", minimum_age=1, maximum_age=99),
        no_declaration=None,
    )

    immich_id = Maybe(
        decider="has_immich_id",
        yes_declaration=Faker("uuid4", cast_to=None),
        no_declaration=None,
    )

    class Params:
        has_birthday = Faker("boolean")
        has_immich_id = Faker("boolean")


class FortuneFactory(DjangoModelFactory[Fortune]):
    class Meta:
        model = Fortune

    id = Faker("random_int")
    author = SubFactory(AuthorFactory)
    text = Faker("paragraph")
    date = Maybe(
        decider="has_date",
        yes_declaration=Faker(
            "date_between_dates", date_start=SelfAttribute("..author.birthday")
        ),
        no_declaration=None,
    )
    hidden = False

    class Params:
        has_date = Faker("boolean")


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


class ImmichPersonResponseDtoFactory(Factory):
    class Meta:
        model = PersonResponseDto

    birth_date = Faker("date_of_birth", minimum_age=1)
    id = Faker("uuid4")
    is_favorite = Faker("boolean")
    is_hidden = False
    name = Faker("first_name")

    @lazy_attribute
    def thumbnail_path(self) -> str:
        return f"/data/thumbs/{uuid4()}/58/08/{self.id}.jpeg"


class ImmichAssetResponseDtoFactory(Factory):
    class Meta:
        model = AssetResponseDto

    id = Faker("uuid4")

    thumbhash = "MWVhOTRiMTgzYTQ2MTcwODI4ZDlhMDA1YTQ0Y2RhYWUzMjYyMDQ1Ngo="
    checksum = thumbhash
    local_date_time = Faker("past_date", start_date="-10y")
    file_created_at = Faker("past_date", start_date=SelfAttribute("..local_date_time"))
    file_modified_at = Faker("past_date", start_date=SelfAttribute("..file_created_at"))
    created_at = Faker("past_date", start_date=SelfAttribute("..file_created_at"))
    updated_at = Faker("past_date", start_date=SelfAttribute("..created_at"))
    duration = None
    has_metadata = True
    height = 1
    width = 1
    is_archived = False
    is_edited = False
    is_favorite = Faker("boolean")
    is_offline = False
    is_trashed = False
    original_path = "tests/data/1px.jpeg"
    original_file_name = "1px.jpeg"
    original_mime_type = "image/jpeg"
    visibility = AssetVisibility.TIMELINE
    owner_id = Faker("uuid4")
    type = AssetTypeEnum.IMAGE
