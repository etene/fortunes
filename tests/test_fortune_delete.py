from django.contrib import messages
import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Fortune
from tests.tools import assert_message

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_delete_fortune(
    fortune: Fortune,
    async_client: AsyncClient,
):
    assert fortune.deleted is False
    # a first call to delete simply sets the boolean to True
    soft_deletion_response = await async_client.post(
        f"/{fortune.id}/delete/", query_params={"next": "/some/path/"}
    )
    assert soft_deletion_response.status_code == HTTPStatus.FOUND
    assert soft_deletion_response.headers["Location"] == "/some/path/"
    assert_message(
        soft_deletion_response,
        message="La citation a été mise à la corbeille.",
        level=messages.INFO,
    )
    await fortune.arefresh_from_db()
    assert fortune.deleted is True
    # A second call really deletes the fortune
    deletion_response = await async_client.post(f"/{fortune.id}/delete/")
    assert deletion_response.status_code == HTTPStatus.FOUND
    # Default redirect is to /
    assert deletion_response.headers["Location"] == "/"
    assert_message(
        deletion_response,
        message="La citation a été supprimée définitivement.",
        level=messages.WARNING,
    )
    with pytest.raises(Fortune.DoesNotExist):
        await fortune.arefresh_from_db()
