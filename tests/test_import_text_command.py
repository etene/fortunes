from pathlib import Path
from django.core.management import call_command
import pytest

from fortunes.app.models import Fortune
from tests.factories import AsyncFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("date_format", ("%d/%m/%Y", "%d/%m/%y"))
def test_import_fortunes_text(
    tmp_path: Path, fortune_factory: AsyncFactory[Fortune], date_format: str
):
    fortunes_to_import = fortune_factory.build_batch(500)
    fortunes_text = "\n".join(
        (f"* {i.date.strftime(date_format)} {i.text}" for i in fortunes_to_import)  # type: ignore[union-attr]
    )
    text_file = tmp_path.joinpath("fortunes.txt")
    text_file.write_text(fortunes_text)
    call_command("import_text", "--author", "Quelq1", str(text_file))
    for to_import, imported in zip(fortunes_to_import, Fortune.objects.with_authors()):
        assert to_import.text == imported.text
        assert to_import.date == imported.date
        assert imported.author.name == "Quelq1"
