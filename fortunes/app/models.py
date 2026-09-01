from django.db import models

# Create your models here.


class Author(models.Model):
    name = models.TextField(null=False, blank=False, unique=True)
    birthday = models.DateField(null=True)
    immich_id = models.UUIDField(null=True)

    def __str__(self) -> str:
        return self.name


class FortuneQuerySet(models.QuerySet["Fortune"]):
    def with_authors(self) -> "FortuneQuerySet":
        return self.select_related("author")

    def current(self) -> "FortuneQuerySet":
        return self.filter(deleted=False)

    def trashed(self) -> "FortuneQuerySet":
        return self.filter(deleted=True)

    def with_author_names(self) -> "FortuneQuerySet":
        return self.annotate(author_name=models.F("author__name"))

    def latest_first(self) -> "FortuneQuerySet":
        return self.order_by("-date")


class Fortune(models.Model):

    objects = FortuneQuerySet().as_manager()

    class Meta:
        get_latest_by = "date"

    author = models.ForeignKey(
        to=Author,
        on_delete=models.PROTECT,
        related_name="fortunes",
    )
    text = models.TextField(
        null=False,
        blank=False,
        help_text="This fortune's text",
        unique=True,
    )
    date = models.DateField(
        null=True,
        help_text="Date on which the fortune was said",
    )
    hidden = models.BooleanField(
        default=False,
        help_text="Whether this fortune should be visible by default",
    )

    deleted = models.BooleanField(
        default=False,
        help_text="Whether this fortune was deleted",
    )

    @property
    def author_age(self) -> int | None:
        if self.date and self.author.birthday:
            return (self.date - self.author.birthday).days // 365
        return None
