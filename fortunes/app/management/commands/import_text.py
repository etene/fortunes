from argparse import FileType
from datetime import date, datetime
from io import TextIOWrapper
from django.core.management import BaseCommand
import re

from fortunes.app.models import Author, Fortune

date_re = re.compile(r"^(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>(\d{4}|\d{2}))\s")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("textfile", type=FileType("rt"))
        parser.add_argument("--author", required=True)

    def handle(self, *args, textfile: TextIOWrapper, author: str, **options):
        auth, created = Author.objects.get_or_create(name=author)
        batch = []
        seen: set[str] = set()
        for line in textfile:
            line = line.strip("\ufeff*").strip()
            date_match = date_re.search(line)
            assert date_match, f"no date for {line!r} !"
            date_parts = {k: int(v) for k, v in date_match.groupdict().items()}
            if (year := date_parts["year"]) < 100:
                if year < datetime.now().date().year - 2000:
                    date_parts["year"] += 2000
                else:
                    date_parts["year"] += 1900
            text = line[date_match.end() :]
            assert text not in seen, f"Duplicate fortune {text!r}"
            seen.add(text)
            batch.append(
                Fortune(
                    text=text,
                    date=date(**date_parts),
                    author=auth,
                )
            )
        if batch:
            Fortune.objects.bulk_create(batch)
