import django_filters

from fortunes.app.models import Fortune


class FortuneFilter(django_filters.FilterSet):
    author_id = django_filters.NumberFilter()
    date = django_filters.DateFilter()
    hidden = django_filters.BooleanFilter()

    class Meta:
        model = Fortune
