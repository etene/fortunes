from django.contrib import messages
from django.core.paginator import AsyncPaginator

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from io import StringIO
import csv
from django.shortcuts import aget_object_or_404, render
from random import randint
from datetime import UTC, datetime
from fortunes.app.filters import build_fortune_filter
from fortunes.app.forms.fortune import BaseFortuneForm, build_fortune_form_cls
from fortunes.app.views.base import BaseCreateFormView, BaseEditFormView
from fortunes.immich import get_random_image
from fortunes.app.models import Author, Fortune


async def random_fortune(request: HttpRequest) -> HttpResponse:
    non_hidden_fortunes = Fortune.objects.current().exclude(hidden=True).with_authors()

    if not (fortune_count := await non_hidden_fortunes.acount()):
        return HttpResponseNotFound(content="No fortunes")

    random_fortune_offset = randint(0, fortune_count - 1)
    random_fortune = await non_hidden_fortunes[
        random_fortune_offset : random_fortune_offset + 1
    ].aget()
    context = {
        "fortune": random_fortune,
        "display_images": True,
        "authors": [i async for i in Author.objects.all()],
    }
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
    context = {
        "fortune": fortune,
        "display_images": True,
        "authors": [i async for i in Author.objects.all()],
    }
    return render(request, "app/detail.html", context)


async def fortune_trashcan(request: HttpRequest) -> HttpResponse:
    # TODO: factorize with fortune_list
    fortune_qs = Fortune.objects.trashed().with_authors().latest_first()
    fortune_filter = await build_fortune_filter(
        data=request.GET,
        queryset=fortune_qs,
    )
    context = {
        "fortunes": [i async for i in fortune_filter.qs],
        "search_form": fortune_filter.form,
        "display_search_form": fortune_filter.data
        and any(fortune_filter.data.values()),
        "authors": [i async for i in Author.objects.all()],  # TODO factorize
    }
    return render(request, "app/fortune_list.html", context)


async def fortune_list(request: HttpRequest) -> HttpResponse:
    fortune_qs = Fortune.objects.with_authors().current().latest_first()
    fortune_filter = await build_fortune_filter(
        data=request.GET,
        queryset=fortune_qs,
    )
    paginator = AsyncPaginator(fortune_filter.qs, per_page=20)
    page = await paginator.aget_page(request.GET.get("page"))
    searched = fortune_filter.data and any(fortune_filter.data.values())
    if result_count := await fortune_filter.qs.acount():
        if searched:
            messages.add_message(
                request=request,
                level=messages.SUCCESS,
                message=f"{result_count} citations trouvées",
                extra_tags="info",
            )
        pages = [
            i
            async for i in paginator.aget_elided_page_range(  # type: ignore[attr-defined]
                number=page.number,
                on_each_side=3,
                on_ends=2,
            )
        ]
    else:
        messages.add_message(
            request=request,
            level=messages.WARNING,
            message="Aucune citation trouvée",
            extra_tags="warning",
        )
        pages = None

    context = {
        "fortunes": [i async for i in page],
        "search_form": fortune_filter.form,
        "display_search_form": searched,
        "authors": [i async for i in Author.objects.all()],  # TODO factorize
        "pages": pages,
        "current_page": page.number,
        "ellipsis": paginator.ELLIPSIS,
    }
    return render(request, "app/fortune_list.html", context)


class FortuneEditFormView(BaseEditFormView[Fortune]):
    template = "app/edit_fortune.html"

    async def get_form_class(self) -> type[BaseFortuneForm]:
        return await build_fortune_form_cls()

    def get_redirect_path(self, instance: Fortune) -> str:
        return f"/{instance.pk}/"


class FortuneCreateFormView(BaseCreateFormView[Fortune]):
    template = "app/edit_fortune.html"

    async def get_form_class(self) -> type[BaseFortuneForm]:
        return await build_fortune_form_cls()

    def get_redirect_path(self, instance: Fortune) -> str:
        return f"/{instance.pk}/"


async def delete_fortune(request: HttpRequest, fortune_id: int):
    fortune = await aget_object_or_404(Fortune, pk=fortune_id)
    if fortune.deleted:
        await fortune.adelete()
    else:
        fortune.deleted = True
        await fortune.asave(update_fields=("deleted",))

    return HttpResponseRedirect(redirect_to=request.GET.get("next", "/"))


async def fortune_export(request: HttpRequest):

    allowed_fields: tuple[str, ...] = ("id", "date", "author_name", "text", "hidden")
    exported_fields = allowed_fields
    if raw_fields := request.GET.get("fields"):
        requested_fields = set(filter(None, raw_fields.split(",")))
        exported_fields = tuple(filter(lambda y: y in requested_fields, allowed_fields))
    if not exported_fields:
        return HttpResponseBadRequest(
            content="One or more of the following comma-separated fields "
            "is required as the 'fields' GET parameter:\n" + ", ".join(allowed_fields)
        )
    fortune_qs = Fortune.objects.current().latest_first()
    if "author_name" in exported_fields:
        fortune_qs = fortune_qs.with_author_names()

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
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; filename="fortunes-export.csv"',
        },
    )
