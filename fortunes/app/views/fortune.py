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

from django_filters import FilterSet
from fortunes.app.filters import build_fortune_filter
from fortunes.app.forms.fortune import BaseFortuneForm, build_fortune_form_cls
from fortunes.app.views.base import (
    BaseCreateFormView,
    BaseEditFormView,
    BaseFortunesDeleteView,
    BaseFortunesListView,
    BaseFortunesView,
)
from fortunes.immich import get_random_image
from fortunes.app.models import Fortune, FortuneQuerySet


class RandomFortuneView(BaseFortunesView[Fortune]):

    async def get_queryset(self) -> FortuneQuerySet:
        assert isinstance(qs := await super().get_queryset(), FortuneQuerySet)
        return qs.current().exclude(hidden=True).with_authors()

    async def get(self, request: HttpRequest) -> HttpResponse:
        queryset = await self.get_queryset()
        if not (fortune_count := await queryset.acount()):
            return HttpResponseNotFound(content="No fortunes")
        random_fortune_offset = randint(0, fortune_count - 1)
        random_fortune = await queryset[
            random_fortune_offset : random_fortune_offset + 1
        ].aget()
        return render(
            request=request,
            template_name="app/index.html",
            context=await self.get_context_data()
            | {
                "fortune": random_fortune,
                "page_title": "Au hasard | Fortunes",
                "display_images": True,
            },
        )


async def random_image(request: HttpRequest, fortune_id: int) -> HttpResponse:
    try:
        fortune = await Fortune.objects.with_authors().aget(pk=fortune_id)
    except Fortune.DoesNotExist:
        return HttpResponseNotFound()
    image_data, image_bytes = await get_random_image(
        around=(
            datetime(
                year=fortune.date.year,
                month=fortune.date.month,
                day=fortune.date.day,
                hour=12,
                tzinfo=UTC,
            )
            if fortune.date
            else None
        ),
        with_person=fortune.author,
    )
    image_name = f"{fortune.author.name} le {image_data.local_date_time.strftime("%x")}"
    return HttpResponse(
        content=image_bytes,
        headers={
            "content-type": "image/jpg",
            "content-disposition": f'inline; filename="{image_name}"',
        },
    )


class FortuneDetailView(BaseFortunesView[Fortune]):

    async def get_queryset(self) -> QuerySet[Fortune]:
        assert isinstance(qs := await super().get_queryset(), FortuneQuerySet)
        return qs.with_authors()

    async def get(self, request, pk: int):
        fortune = await aget_object_or_404(await self.get_queryset(), pk=pk)
        context = await self.get_context_data() | {
            "fortune": fortune,
            "display_images": True,
            "title": f"#{fortune.id} | Fortunes",
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

    async def get_queryset(self) -> QuerySet[Fortune]:
        return (await super().get_queryset()).with_authors().current().latest_first()  # type: ignore[attr-defined]

    def request_was_filtered(self, filter_: FilterSet) -> bool:
        if not super().request_was_filtered(filter_):
            return False
        assert (data := filter_.data)
        data_with_values = {k: v for k, v in data.items() if v}
        # assume the request has been filtered only if the filter form hasn't its default value
        return data_with_values != {"hidden": "false"}


class FortuneTrashcanView(FortuneListView):
    RESULTS_FOUND_MSG = "{result_count} citation(s) supprimée(s) trouvée(s)"
    NO_RESULTS_MSG = "Aucune citation supprimée"

    async def get_queryset(self) -> QuerySet[Fortune]:
        return (await BaseFortunesView.get_queryset(self)).trashed().with_authors().latest_first()  # type: ignore[attr-defined]


class FortuneEditFormView(BaseEditFormView[Fortune]):
    template = "app/edit_fortune.html"

    async def get_context_data(self) -> dict[str, Any]:
        return (await super().get_context_data()) | {
            "title": "Modifier une citation | Fortunes"
        }

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


class FortuneDeleteView(BaseFortunesDeleteView[Fortune]):
    DELETION_SUCCESS_MSG = "La citation #{instance.id} a été supprimée définitivement."
    NOT_FOUND_MSG = "Aucune citation correspondante trouvée."
    TRASHED_MSG = "La citation a été mise à la corbeille."

    async def perform_deletion(self, instance: Fortune) -> bool:
        if instance.deleted:
            return await super().perform_deletion(instance)
        instance.deleted = True
        await instance.asave(update_fields=("deleted",))
        messages.add_message(
            request=self.request,
            level=messages.INFO,
            message="La citation a été mise à la corbeille.",
            extra_tags="info",
        )
        return True


class ToggleHiddenFortuneView(BaseFortunesView[Fortune]):
    async def post(self, request: HttpRequest, fortune_id: int) -> HttpResponse:
        fortune = await aget_object_or_404(await self.get_queryset(), pk=fortune_id)
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
        queryset = await self.get_queryset()
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
