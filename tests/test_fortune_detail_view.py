import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Fortune
from tests.tools import HTMLElement, assert_html

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_get_fortune(
    fortune: Fortune,
    async_client: AsyncClient,
):
    response = await async_client.get(f"/{fortune.id}/")
    assert response.status_code == HTTPStatus.OK
    assert_html(
        response.content,
        # There is a blockquote with the text
        HTMLElement(
            tag="blockquote",
            attrs={"class": "blockquote"},
            content=fortune.text,
        ),
        # There is an image at the bottom
        HTMLElement(
            tag="img",
            attrs={
                "src": f"/random_image/{fortune.id}/",
                "class": "card-img-bottom",
            },
        ),
    )
