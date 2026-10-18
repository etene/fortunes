from django.http import HttpRequest, HttpResponse
from django.shortcuts import aget_object_or_404
from fortunes import immich
from fortunes.app.forms.author import AuthorForm
from fortunes.app.models import Author
from fortunes.app.views.base import BaseCreateFormView, BaseEditFormView


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


async def author_thumbnail(request: HttpRequest, pk: int):
    author = await aget_object_or_404(Author, pk=pk)
    thumbnail = await immich.get_person_thumbnail(author)
    return HttpResponse(
        content=thumbnail,
        headers={"content-type": "image/jpg"},
    )
