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
