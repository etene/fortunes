import django_filters
import django_filters.widgets

from fortunes.app.forms.base import FortuneDateInput
from fortunes.app.models import Author, Fortune


class BaseFortuneFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        label="À partir du",
        widget=FortuneDateInput(format="%Y-%m-%d"),
        method="filter_date",
    )
    end_date = django_filters.DateFilter(
        label="Jusqu'au",
        widget=FortuneDateInput(format="%Y-%m-%d"),
        method="filter_date",
    )
    hidden = django_filters.BooleanFilter(
        widget=django_filters.widgets.BooleanWidget(),
        label="Caché ?",
    )
    text = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Contient",
    )

    def filter_date(self, queryset, field_name, value):
        model_filter_name = {"start_date": "date__gt", "end_date": "date__lt"}[
            field_name
        ]
        return queryset.filter(**{model_filter_name: value})

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
