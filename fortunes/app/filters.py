import django_filters
from django_filters import widgets

from fortunes.app.models import Author, Fortune


class BaseFortuneFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(label="Date")
    hidden = django_filters.BooleanFilter(widget=widgets.BooleanWidget(), label="Caché")
    text = django_filters.CharFilter(lookup_expr="icontains", label="Texte")

    class Meta:
        model = Fortune
        fields: dict[str, str] = {}


async def build_fortune_filter(data, queryset) -> BaseFortuneFilter:
    author_choices: list[tuple[int | None, str]] = [(None, "Tous")]
    async for author_id, author_name in Author.objects.values_list("id", "name"):
        assert isinstance(author_id, int)
        assert isinstance(author_name, str)
        author_choices.append((author_id, author_name))

    class FortuneFilter(BaseFortuneFilter):
        author_id = django_filters.TypedChoiceFilter(
            label="Auteur",
            choices=author_choices,
        )

    return FortuneFilter(data, queryset)
