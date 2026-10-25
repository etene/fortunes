from typing import Any
import pytest
from django.test import AsyncClient
from datetime import date
from http import HTTPStatus
from fortunes.app.models import Author, Fortune
from tests.tools import match_html_elements

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


@pytest.mark.parametrize(
    ("payload", "expected_attrs"),
    (
        (
            {
                "text": "test",
                "date": "20/07/2026",
            },
            {
                "text": "test",
                "date": date(year=2026, month=7, day=20),
            },
        ),
        (
            {
                "text": "test  ",
                "date": "",
            },
            {
                "text": "test",
                "date": None,
            },
        ),
    ),
)
async def test_create_fortune(
    async_client: AsyncClient,
    author: Author,
    payload: dict[str, Any],
    expected_attrs: dict[str, Any],
):
    response = await async_client.post(
        "/new/",
        data={
            "author_id": author.id,
            **payload,
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    created_fortune = await Fortune.objects.with_authors().aget()
    for attname, expected_value in expected_attrs.items():
        assert getattr(created_fortune, attname) == expected_value
    assert created_fortune.author == author
    assert response.headers["Location"] == f"/{created_fortune.id}/"


async def test_create_duplicate_fortune(
    fortune: Fortune,
    async_client: AsyncClient,
):
    response = await async_client.post(
        "/new/",
        data={
            "author_id": fortune.author.id,
            "text": fortune.text,
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert await Fortune.objects.filter(text=fortune.text).acount() == 1
    match_html_elements(
        html=response.content,
        tag="div",
        attrs={"class": "invalid-feedback d-block"},
        contains="Il existe déjà une autre citation avec le même texte",
        expected_matches=1,
    )
