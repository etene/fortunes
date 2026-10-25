from typing import Any, ClassVar
from django.contrib import messages
from django.contrib.messages import add_message
from django.db import IntegrityError
from django.db.models import QuerySet
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
from fortunes.app.views.base import (
    BaseCreateFormView,
    BaseEditFormView,
    BaseFortunesListView,
    BaseFortunesView,
)
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


class FortuneListView(BaseFortunesListView[Fortune]):

    template = "app/fortune_list.html"

    RESULTS_FOUND_MSG = "{result_count} citation(s) trouvée(s)"
    NO_RESULTS_MSG = "Aucune citation trouvée"

    async def get_context_data(self) -> dict[str, Any]:
        data = await super().get_context_data()
        data["exportable_fields"] = FortuneCSVExportView.EXPORTABLE_FIELDS
        return data

    async def get_filter(self, queryset: QuerySet[Fortune], request: HttpRequest):
        return await build_fortune_filter(data=request.GET, queryset=queryset)

    def get_queryset(self) -> QuerySet[Fortune]:
        return super().get_queryset().with_authors().current().latest_first()  # type: ignore[attr-defined]


class FortuneTrashcanView(FortuneListView):
    RESULTS_FOUND_MSG = "{result_count} citation(s) supprimée(s) trouvée(s)"
    NO_RESULTS_MSG = "Aucune citation supprimée"

    def get_queryset(self) -> QuerySet[Fortune]:
        return BaseFortunesListView.get_queryset(self).trashed().with_authors().latest_first()  # type: ignore[attr-defined]


class FortuneEditFormView(BaseEditFormView[Fortune]):
    template = "app/edit_fortune.html"

    async def get_form_class(self) -> type[BaseFortuneForm]:
        return await build_fortune_form_cls()

    def get_redirect_path(self, instance: Fortune) -> str:
        return f"/{instance.pk}/"


class FortuneCreateFormView(BaseCreateFormView[Fortune]):
    template = "app/edit_fortune.html"

    def handle_integrity_error(self, err: IntegrityError) -> tuple[str, str]:
        if str(err) == "UNIQUE constraint failed: app_fortune.text":
            return "text", "Il existe déjà une autre citation avec le même texte"
        return super().handle_integrity_error(err)

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


class ToggleHiddenFortuneView(BaseFortunesView[Fortune]):
    async def post(self, request: HttpRequest, fortune_id: int) -> HttpResponse:
        fortune = await aget_object_or_404(Fortune, pk=fortune_id)
        if fortune.hidden:
            add_message(
                request=request,
                level=messages.INFO,
                message="La citation n'est plus cachée",
            )
        else:
            add_message(
                request=request, level=messages.INFO, message="La citation a été cachée"
            )
        fortune.hidden = not fortune.hidden
        await fortune.asave(update_fields=("hidden",))
        return HttpResponseRedirect(f"/{fortune.id}/")


class FortuneCSVExportView(FortuneListView):

    EXPORTABLE_FIELDS: ClassVar[dict[str, str]] = {
        "id": "Numéro",
        "date": "Date",
        "author_name": "Auteur",
        "text": "Citation",
    }

    async def post(self, request: HttpRequest) -> HttpResponse:
        queryset = self.get_queryset()
        filter_ = await self.get_filter(queryset=queryset, request=request)
        allowed_fields = tuple(self.EXPORTABLE_FIELDS)
        exported_fields = allowed_fields
        requested_fields = {
            name
            for name, value in dict(request.POST).items()
            if "csrf_token" not in name and value == ["on"]
        }
        if requested_fields:
            exported_fields = tuple(
                filter(lambda y: y in requested_fields, allowed_fields)
            )
        if not exported_fields:
            return HttpResponseBadRequest(
                content="One or more of the following fields "
                "is required in the POST data:\n" + ", ".join(allowed_fields)
            )
        fortune_qs = filter_.qs
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
