from http import HTTPMethod, HTTPStatus
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from io import StringIO
import csv
from django.shortcuts import aget_object_or_404, render
from random import randint
from datetime import UTC, date, datetime
from fortunes.app.filters import build_fortune_filter
from fortunes.app.forms import build_fortune_form
from fortunes.immich import get_random_image
from .models import Author, Fortune


async def random_fortune(request: HttpRequest) -> HttpResponse:
    non_hidden_fortunes = Fortune.objects.current().exclude(hidden=True).with_authors()
    fortune_count = await non_hidden_fortunes.acount()
    random_fortune_offset = randint(0, fortune_count - 1)
    random_fortune = await non_hidden_fortunes[
        random_fortune_offset : random_fortune_offset + 1
    ].aget()
    context = {"fortune": random_fortune, "display_images": True}
    return render(request, "app/index.html", context)


async def random_image(request: HttpRequest, fortune_id: int) -> HttpResponse:
    try:
        fortune = await Fortune.objects.with_authors().aget(pk=fortune_id)
    except Fortune.DoesNotExist:
        return HttpResponseNotFound()
    image_bytes = await get_random_image(
        taken_after=(
            datetime(year=fortune.date.year, month=1, day=1, tzinfo=UTC)
            if fortune.date
            else None
        ),
        taken_before=(
            datetime(year=fortune.date.year + 1, month=1, day=1, tzinfo=UTC)
            if fortune.date
            else None
        ),
        with_person=fortune.author,
    )
    return HttpResponse(
        content=image_bytes,
        headers={"content-type": "image/jpg"},
    )


async def single_fortune(request: HttpRequest, fortune_id: int):
    fortune = await aget_object_or_404(Fortune.objects.with_authors(), pk=fortune_id)
    context = {"fortune": fortune, "display_images": True}
    return render(request, "app/detail.html", context)


async def fortune_trashcan(request: HttpRequest) -> HttpResponse:
    context = {
        "fortunes": [
            i
            async for i in Fortune.objects.trashed()
            .with_authors()
            .order_by("-date")
            .all()
        ]
    }
    return render(request, "app/fortune_list.html", context)


async def fortune_list(request: HttpRequest) -> HttpResponse:
    fortune_qs = Fortune.objects.with_authors().current().order_by("-date")
    fortune_filter = await build_fortune_filter(
        data=request.GET,
        queryset=fortune_qs,
    )
    context = {
        "fortunes": [i async for i in fortune_filter.qs],
        "search_form": fortune_filter.form,
    }
    return render(request, "app/fortune_list.html", context)


async def new_fortune(request: HttpRequest) -> HttpResponse:
    authors = [i async for i in Author.objects.all()]
    if request.method == HTTPMethod.GET:
        context = {
            "authors": authors,
            "selected_author": authors[0] if authors else None,
            "fortune_date": date.today().isoformat(),
            "form": await build_fortune_form(),
        }
        return render(request, "app/edit_fortune.html", context)
    elif request.method == HTTPMethod.POST:
        form = await build_fortune_form(data=request.POST)
        if form.is_valid():
            created_fortune = await form.create_fortune()
            return HttpResponseRedirect(f"/{created_fortune.id}/")
        context = {
            "authors": authors,
            "selected_author": authors[0] if authors else None,
            "fortune_date": date.today().isoformat(),
            "form": form,
            "form_target": "/new/",
        }
    else:
        assert False
    return render(
        request=request,
        template_name="app/edit_fortune.html",
        context=context,
        status=HTTPStatus.BAD_REQUEST,
    )


async def edit_fortune(request: HttpRequest, fortune_id: int) -> HttpResponse:
    fortune = await aget_object_or_404(Fortune.objects.with_authors(), pk=fortune_id)
    context = {"fortune": fortune, "display_images": True}
    status = HTTPStatus.OK
    if request.method == HTTPMethod.POST:
        form = await build_fortune_form(request.POST)
        if form.is_valid():
            await form.update_fortune(fortune)
            return HttpResponseRedirect(f"/{fortune.id}/")
        else:
            status = HTTPStatus.BAD_REQUEST
    else:
        form = await build_fortune_form(
            data={
                "fortune_text": fortune.text,
                "fortune_date": fortune.date,
                "fortune_author_id": fortune.author_id,
            }
        )
    context["form"] = form
    context["form_target"] = f"/{fortune.id}/edit/"
    return render(request, "app/edit_fortune.html", context, status=status)


async def delete_fortune(request: HttpRequest, fortune_id: int):
    fortune = await aget_object_or_404(Fortune, pk=fortune_id)
    if fortune.deleted:
        await fortune.adelete()
    else:
        fortune.deleted = True
        await fortune.asave(update_fields=("deleted",))

    return HttpResponseRedirect(redirect_to=request.GET.get("next", "/"))


async def fortune_export(request: HttpRequest):

    allowed_fields: tuple[str, ...] = ("id", "date", "author", "text", "hidden")
    exported_fields = allowed_fields
    if raw_fields := request.GET.get("fields"):
        requested_fields = set(filter(None, raw_fields.split(",")))
        exported_fields = tuple(filter(lambda y: y in allowed_fields, requested_fields))
    if not exported_fields:
        # TODO
        raise ValueError
    fortune_qs = Fortune.objects.with_authors().current().order_by("-date")
    fortune_filter = await build_fortune_filter(
        data=request.GET,
        queryset=fortune_qs,
    )
    csv_output = StringIO()
    csv_writer = csv.DictWriter(f=csv_output, fieldnames=exported_fields)
    csv_writer.writeheader()
    async for fortune in fortune_filter.qs.values(*exported_fields):
        csv_writer.writerow(fortune)
    return HttpResponse(
        content=csv_output.getvalue(),
        headers={"Content-Type": "text/csv"},
    )
