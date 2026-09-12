from typing import Any
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from http import HTTPMethod, HTTPStatus
from django.shortcuts import aget_object_or_404, render
from fortunes.app.forms.author import AuthorForm
from fortunes.app.models import Author


async def author_edit(request: HttpRequest, author_id: int) -> HttpResponse:
    author = await aget_object_or_404(Author.objects.all(), pk=author_id)
    context: dict[str, Any] = {"author": author}
    status = HTTPStatus.OK
    if request.method == HTTPMethod.POST:
        form = AuthorForm(data=request.POST)
        if form.is_valid():
            await form.update(author)
            return HttpResponseRedirect(f"/authors/{author.id}/")
        else:
            status = HTTPStatus.BAD_REQUEST
    elif request.method == HTTPMethod.GET:
        form = AuthorForm.from_instance(author)
    else:
        raise NotImplementedError
    context["form"] = form
    context["form_target"] = f"/{author.id}/edit/"
    return render(request, "app/edit_author.html", context, status=status)
