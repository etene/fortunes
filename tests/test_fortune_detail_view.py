import pytest
from django.test import AsyncClient
from http import HTTPStatus
from fortunes.app.models import Fortune
from tests.tools import match_html_elements

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_get_fortune(
    fortune: Fortune,
    async_client: AsyncClient,
):
    response = await async_client.get(f"/{fortune.id}/")
    assert response.status_code == HTTPStatus.OK
    match_html_elements(
        response.content,
        # There is a blockquote with the text
        tag="blockquote",
        attrs={"class": "blockquote"},
        contains=fortune.text,
        expected_matches=1,
    )
    match_html_elements(
        response.content,
        # There is an image at the bottom
        tag="img",
        attrs={
            "src": f"/random_image/{fortune.id}/",
            "class": "card-img-bottom",
        },
    )
