from fortunes.app.forms.author import AuthorForm
from fortunes.app.models import Author
from fortunes.app.views.base import BaseAsyncFormView


class AuthorFormView(BaseAsyncFormView[Author]):
    template = "app/edit_author.html"

    async def get_form_class(self) -> type[AuthorForm]:
        return AuthorForm


# TODO CBV
