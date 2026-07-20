from uuid import UUID
from immichpy import AsyncClient
from datetime import datetime
from django.conf import settings
from immichpy.client.generated.models.asset_type_enum import AssetTypeEnum
from immichpy.client.generated.models.random_search_dto import RandomSearchDto

from fortunes.app.models import Author


async def _find_person_id(immich: AsyncClient, name: str) -> UUID:
    response = await immich.search.search_person(name=name)
    for i in response:
        if i.name.lower() == name.lower():
            return i.id
    raise LookupError(f"No immich person found with {name=}")


# {"page":1,"withExif":true,"query":"portrait","takenAfter":"2018-10-10T00:00:00.000Z","takenBefore":"2019-10-23T23:59:59.999Z","personIds":["58089707-902e-458c-a503-47000664b470"],"type":"IMAGE","language":"fr"}
async def get_random_image(
    taken_before: datetime,
    taken_after: datetime,
    with_person: Author,
    search_term: str,
) -> bytes:

    async with AsyncClient(
        api_key=settings.IMMICH_API_KEY,
        base_url=settings.IMMICH_BASE_URL,
    ) as immich:
        if with_person.immich_id is None:
            with_person.immich_id = await _find_person_id(immich, name=with_person.name)
            await with_person.asave()
        search_criteria = RandomSearchDto(
            withExif=True,
            takenAfter=taken_after,
            takenBefore=taken_before,
            type=AssetTypeEnum.IMAGE,
            personIds=[with_person.immich_id],
            size=1,
        )
        search_results = await immich.search.search_random(search_criteria)
        chosen_one = search_results[0]
        return await immich.assets.download_asset(id=chosen_one.id)
