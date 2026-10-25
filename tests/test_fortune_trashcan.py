from http import HTTPStatus
from django.contrib import messages
import pytest
from django.test import AsyncClient
from fortunes.app.models import Fortune
from tests.factories import AsyncFactory
from tests.tools import assert_message

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_get_trashed_fortunes(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
):
    not_deleted = await fortune_factory()
    deleted = await fortune_factory(deleted=True)
    other_deleted = await fortune_factory()
    response = await async_client.get(
        "/trashcan/", query_params={"author_id": deleted.author_id}
    )
    assert response.status_code == HTTPStatus.OK
    assert_message(
        response,
        level=messages.INFO,
        message="1 citation(s) supprimée(s) trouvée(s)",
    )
    html = response.content.decode()
    assert not_deleted.text not in html
    assert other_deleted.text not in html
