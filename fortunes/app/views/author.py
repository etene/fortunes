from django.contrib import messages
from django.db.models import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.views.decorators.cache import cache_control
from django.shortcuts import aget_object_or_404
from fortunes import immich
from fortunes.app.forms.author import AuthorForm
from fortunes.app.models import Author
from fortunes.app.views.base import (
    BaseCreateFormView,
    BaseEditFormView,
    BaseFortunesDeleteView,
)


class AuthorEditFormView(BaseEditFormView[Author]):
    template = "app/edit_author.html"

    async def get_form_class(self) -> type[AuthorForm]:
        return AuthorForm

    def get_redirect_path(self, instance: Author) -> str:
        return "/"


class AuthorCreateFormView(BaseCreateFormView[Author]):
    template = "app/edit_author.html"

    async def get_form_class(self) -> type[AuthorForm]:
        return AuthorForm

    def get_redirect_path(self, instance: Author) -> str:
        return f"/author/{instance.pk}/edit"


@cache_control(private=True, max_age=3600 * 24)
async def author_thumbnail(request: HttpRequest, pk: int):
    author = await aget_object_or_404(Author, pk=pk)
    thumbnail = await immich.get_person_thumbnail(author)
    return HttpResponse(
        content=thumbnail,
        headers={"content-type": "image/jpg"},
    )


class AuthorDeleteView(BaseFortunesDeleteView[Author]):
    DELETION_SUCCESS_MSG = "L'auteur {instance.name!r} a été supprimé"
    NOT_FOUND_MSG = "Aucun auteur correspondant trouvé"

    async def perform_deletion(self, instance: Author) -> bool:
        try:
            return await super().perform_deletion(instance)
        except ProtectedError:
            messages.add_message(
                request=self.request,
                level=messages.ERROR,
                message=f"Impossible de supprimer {instance.name}, qui a encore des citations.",
                extra_tags="error",
            )
            return False
