from http import HTTPStatus
from django.contrib import messages
import pytest
from django.test import AsyncClient
from fortunes.app.models import Fortune
from tests.factories import AsyncFactory
from tests.tools import assert_message

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


@pytest.mark.parametrize(
    ("initially_hidden", "message"),
    (
        (False, "La citation a été cachée"),
        (True, "La citation n'est plus cachée"),
    ),
)
async def test_toggle_fortune_hidden(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
    initially_hidden: bool,
    message: str,
):
    fortune = await fortune_factory(hidden=initially_hidden)
    response = await async_client.post(f"/{fortune.id}/toggle_hidden/")
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers["location"] == f"/{fortune.id}/"
    assert_message(
        response=response,
        level=messages.INFO,
        message=message,
    )
    await fortune.arefresh_from_db()
    assert fortune.hidden is not initially_hidden
