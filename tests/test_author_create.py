from http import HTTPStatus
from unittest.mock import call
import pytest
from uuid import uuid4
from django.test import AsyncClient
from fortunes.app.models import Author
from tests.factories import ImmichPersonResponseDtoFactory
from tests.immich_mock import ImmichClientMock
from tests.tools import match_html_elements

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_create_author_with_immich_id(
    async_client: AsyncClient,
):
    fake_immich_id = uuid4()
    response = await async_client.post(
        path="/author/new/",
        data={
            "name": "Jean-Michel",
            "immich_id": fake_immich_id,
        },
    )
    assert response.status_code == HTTPStatus.FOUND
    created_author = await Author.objects.aget(name="Jean-Michel")
    assert created_author.immich_id == fake_immich_id
    assert response.headers["location"] == f"/author/{created_author.id}/edit/"


async def test_get_author_create_form(
    async_client: AsyncClient,
):
    response = await async_client.get("/author/new/")
    assert response.status_code == HTTPStatus.OK
    match_html_elements(
        response.content,
        tag="input",
        attrs={
            "type": "text",
            "name": "name",
            "class": "form-control",
            "placeholder": "Nom",
            "required": None,
            "id": "id_name",
        },
        expected_matches=1,
    )
    match_html_elements(
        response.content,
        tag="input",
        attrs={
            "type": "date",
            "class": "form-control",
            "placeholder": "Date de naissance",
            "id": "id_birthday",
            "name": "birthday",
        },
        expected_matches=1,
    )
    match_html_elements(
        response.content,
        tag="input",
        attrs={
            "type": "text",
            "name": "immich_id",
            "class": "form-control",
            "placeholder": "ID utilisateur Immich",
            "style": "font-family:monospace;",
            "id": "id_immich_id",
        },
        expected_matches=1,
    )


@pytest.mark.parametrize("author_in_immich", (True, False))
async def test_create_author_without_immich_id(
    async_client: AsyncClient,
    immich_mock: ImmichClientMock,
    author_in_immich: bool,
):
    immich_author = ImmichPersonResponseDtoFactory.create()
    if author_in_immich:
        immich_mock.persons.append(immich_author)
    response = await async_client.post(
        path="/author/new/",
        data={"name": immich_author.name},
    )
    assert response.status_code == HTTPStatus.FOUND
    assert immich_mock.search_person_mock.call_args_list == [
        call(name=immich_author.name)
    ]
    author = await Author.objects.aget(name=immich_author.name)
    if author_in_immich:
        assert author.immich_id == immich_author.id
    else:
        assert author.immich_id is None
