from immichpy import AsyncClient
from datetime import datetime, timedelta
from django.conf import settings
from immichpy.client.generated.models.asset_response_dto import AssetResponseDto
from immichpy.client.generated.models.asset_type_enum import AssetTypeEnum
from immichpy.client.generated.models.person_response_dto import PersonResponseDto
from immichpy.client.generated.models.random_search_dto import RandomSearchDto
from fortunes.app.models import Author


def immich_client() -> AsyncClient:
    return AsyncClient(
        api_key=settings.IMMICH_API_KEY,
        base_url=settings.IMMICH_BASE_URL,
    )


async def find_person(name: str) -> PersonResponseDto:
    async with immich_client() as immich:
        response = await immich.search.search_person(name=name)
        for i in response:
            if i.name.lower() == name.lower():
                return i
    raise LookupError(f"No immich person found with {name=}")


async def get_random_image(
    with_person: Author,
    around: datetime | None = None,
    search_radius: timedelta = timedelta(weeks=3),
) -> tuple[AssetResponseDto, bytes]:
    if not with_person.immich_id:
        # FIXME get other image ?
        raise LookupError(f"{with_person} has no immich id")
    taken_after, taken_before = None, None
    if around:
        taken_after = around - search_radius
        taken_before = around + search_radius
    async with immich_client() as immich:
        search_criteria = RandomSearchDto(
            withExif=True,
            takenAfter=taken_after,
            takenBefore=taken_before,
            type=AssetTypeEnum.IMAGE,
            personIds=[with_person.immich_id],
            size=100,
        )
        search_results = await immich.search.search_random(search_criteria)
        if not search_results:
            raise LookupError("No image found")  # TODO
        if around:
            # sort results by proximity to "around"
            search_results.sort(
                key=lambda res: abs((around - res.local_date_time).total_seconds())
            )
        chosen_one = search_results[0]
        return chosen_one, await immich.assets.download_asset(id=chosen_one.id)


async def get_person_thumbnail(person: Author) -> bytes:
    if not person.immich_id:
        # TODO return generic thumbnail
        raise LookupError(f"{person} has no immich id")
    async with immich_client() as immich:
        return await immich.people.get_person_thumbnail(id=person.immich_id)
