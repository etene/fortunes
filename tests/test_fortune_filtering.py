from datetime import date
from http import HTTPStatus
import re
from django.contrib import messages
import pytest
from django.test import AsyncClient
from fortunes.app.models import Author, Fortune
from tests.factories import AsyncFactory
from tests.tools import assert_message, match_html_elements

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_filter_fortunes_by_author(
    fortune_factory: AsyncFactory[Fortune],
    author_factory: AsyncFactory[Author],
    async_client: AsyncClient,
):
    author1, author2 = await author_factory.create_batch(2)
    author1_fortunes = await fortune_factory.create_batch(3, author=author1)
    await fortune_factory(author=author2)
    response = await async_client.get(
        "/browse/", query_params={"author_id": author1.id}
    )
    assert response.status_code == HTTPStatus.OK

    fortune_id_spans = match_html_elements(
        response.content,
        tag="span",
        attrs={"class": "font-monospace"},
        contains=re.compile(r"^.*\d+$"),
        expected_matches=3,
    )
    assert {i.content_lines[0] for i in fortune_id_spans} == {
        f"\xa0{i.id}" for i in author1_fortunes
    }
    assert_message(
        response,
        message="3 citation(s) trouvée(s)",
        level=messages.INFO,
    )


async def test_search_fortune_text(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
):
    fortune = await fortune_factory(text="un guéopard")
    other_fortune = await fortune_factory()
    response = await async_client.get("/browse/", query_params={"text": "guéopar"})
    assert response.status_code == HTTPStatus.OK
    html = response.content.decode()
    assert other_fortune.text not in html
    assert fortune.text in html


@pytest.mark.parametrize(
    ("query_params", "expected_fortune_years"),
    (
        ({"start_date": "2022-01-02"}, {2024, 2026}),
        ({"start_date": "2025-12-22"}, {2026}),
        ({"end_date": "2025-02-06"}, {2020, 2024}),
        ({"start_date": "2021-10-31", "end_date": "2025-01-01"}, {2024}),
        ({"end_date": "2019-12-31"}, {}),
    ),
)
async def test_search_fortunes_by_date(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
    query_params: dict[str, str],
    expected_fortune_years: set[int],
):
    fortunes_by_year: dict[int, Fortune] = {
        2020: await fortune_factory(
            date=date(year=2020, month=6, day=23), text="2020 fortune"
        ),
        2024: await fortune_factory(
            date=date(year=2024, month=4, day=20), text="2024 fortune"
        ),
        2026: await fortune_factory(
            date=date(year=2026, month=12, day=30), text="2026 fortune"
        ),
    }
    response = await async_client.get("/browse/", query_params=query_params)
    assert response.status_code == HTTPStatus.OK
    if expected_fortune_years:
        assert_message(
            response,
            level=messages.INFO,
            message=f"{len(expected_fortune_years)} citation(s) trouvée(s)",
        )
    else:
        assert_message(
            response,
            level=messages.WARNING,
            message="Aucune citation trouvée",
        )
    html = response.content.decode()
    for year, fortune in fortunes_by_year.items():
        if year in expected_fortune_years:
            assert fortune.text in html
        else:
            assert fortune.text not in html


async def test_hidden_fortunes_not_visible(
    fortune_factory: AsyncFactory[Fortune],
    async_client: AsyncClient,
):
    fortune = await fortune_factory()
    hidden_fortune = await fortune_factory(hidden=True)
    response = await async_client.get("/browse/")
    assert response.status_code == HTTPStatus.OK
    html = response.content.decode()
    assert fortune.text in html
    assert hidden_fortune.text not in html
