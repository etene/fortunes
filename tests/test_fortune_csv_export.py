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
    reader = csv.DictReader(response.content.decode().splitlines())
    rows = list(reader)
    assert len(rows) == len(fortunes) == 30
    for row, fortune in zip(rows, fortunes):
        assert list(row) == ["id", "date", "author", "text", "hidden"]
        assert row["id"] == str(fortune.id)
        assert row["date"] == str(fortune.date)
        assert row["author"] == str(fortune.author_id)
        assert row["text"] == fortune.text
        assert row["hidden"] == str(fortune.hidden)
