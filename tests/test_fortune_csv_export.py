from http import HTTPStatus
import pytest
from django.test import AsyncClient
import csv

from fortunes.app.models import Author, Fortune
from operator import attrgetter
from tests.factories import AsyncFactory

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_export_fortunes_csv(
    async_client: AsyncClient,
    author: Author,
    fortune_factory: AsyncFactory[Fortune],
):
    fortunes = sorted(
        await fortune_factory.create_batch(30, author=author),
        key=attrgetter("date"),
        reverse=True,
    )
    response = await async_client.get("/export/")
    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"] == "text/csv"
    assert (
        response.headers["Content-Disposition"]
        == 'attachment; filename="fortunes-export.csv"'
    )
    reader = csv.DictReader(response.content.decode().splitlines())
    rows = list(reader)
    assert len(rows) == len(fortunes) == 30
    for row, fortune in zip(rows, fortunes):
        assert list(row) == ["id", "date", "author_name", "text", "hidden"]
        assert row["id"] == str(fortune.id)
        assert row["date"] == str(fortune.date)
        assert row["author_name"] == author.name
        assert row["text"] == fortune.text
        assert row["hidden"] == str(fortune.hidden)


@pytest.mark.parametrize(
    "requested_fields",
    (
        ("id", "author_name", "date"),
        ("id", "text", "text"),
        ("hidden",),
    ),
)
async def test_export_fortunes_csv_custom_fields(
    async_client: AsyncClient,
    author: Author,
    fortune_factory: AsyncFactory[Fortune],
    requested_fields: tuple[str, ...],
):
    await fortune_factory.create_batch(3, author=author)
    fortunes = [i async for i in Fortune.objects.with_author_names().latest_first()]

    response = await async_client.get(
        "/export/", data={"fields": ",".join(requested_fields)}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"] == "text/csv"
    reader = csv.DictReader(response.content.decode().splitlines())
    rows = list(reader)
    assert len(rows) == len(fortunes) == 3
    for row, fortune in zip(rows, fortunes):
        assert set(row) == set(requested_fields)
        for i in requested_fields:
            assert row[i] == str(getattr(fortune, i))
