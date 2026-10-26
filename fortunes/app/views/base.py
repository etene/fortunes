from abc import ABC, abstractmethod
import abc
from typing import TYPE_CHECKING, Any, ClassVar
from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.paginator import AsyncPage, AsyncPaginator
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import aget_object_or_404, render
from django.views.generic import View
import asyncio
from http import HTTPStatus

from django_filters import FilterSet
from fortunes.app.models import Author

if TYPE_CHECKING:
    from fortunes.app.forms.base import AbstractForm
    from django.db.models import Model, QuerySet


class BaseFortunesView[ModelT: Model](ABC, View):

    @classmethod
    def get_model_class(cls) -> type[ModelT]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore[attr-defined]

    async def get_context_data(self) -> dict[str, Any]:
        return {"authors": [i async for i in Author.objects.all()]}


class BaseFortunesListView[ModelT: Model](BaseFortunesView):

    RESULTS_FOUND_MSG: ClassVar[str] = "{result_count} résultat(s)"
    NO_RESULTS_MSG: ClassVar[str] = "Aucun résultat"

    template: ClassVar[str]

    def get_queryset(self) -> QuerySet[ModelT]:
        return self.get_model_class().objects.all()

    @abc.abstractmethod
    async def get_filter(
        self, queryset: QuerySet[ModelT], request: HttpRequest
    ) -> FilterSet: ...

    async def get_page(self, queryset: QuerySet[ModelT]) -> AsyncPage[ModelT]:
        paginator = AsyncPaginator(queryset, per_page=20)
        return await paginator.aget_page(self.request.GET.get("page"))

    def request_was_filtered(self, filter_: FilterSet) -> bool:
        return bool(filter_.data and any(filter_.data.values()))

    async def get(self, request: HttpRequest) -> HttpResponse:
        queryset = self.get_queryset()
        filter_ = await self.get_filter(queryset=queryset, request=request)
        page = await self.get_page(filter_.qs)
        searched = self.request_was_filtered(filter_)
        pages = None

        if result_count := await filter_.qs.acount():
            if searched:
                messages.add_message(
                    request=request,
                    level=messages.INFO,
                    message=self.RESULTS_FOUND_MSG.format(result_count=result_count),
                    extra_tags="info",
                )
            pages = [
                i
                async for i in page.paginator.aget_elided_page_range(  # type: ignore[attr-defined]
                    number=page.number,
                    on_each_side=3,
                    on_ends=2,
                )
            ]
        else:
            messages.add_message(
                request=request,
                level=messages.WARNING,
                message=self.NO_RESULTS_MSG,
                extra_tags="warning",
            )

        context = await self.get_context_data()
        context.update(
            {
                "search_form": filter_.form,
                "display_search_form": searched,
                "fortunes": [i async for i in page],
                "pages": pages,
                "current_page": page.number,
                "ellipsis": page.paginator.ELLIPSIS,
            }
        )
        return render(request, self.template, context)


class BaseFortunesDeleteView[ModelT: Model](BaseFortunesView):

    DELETION_SUCCESS_MSG: ClassVar[str] = "L'objet a été supprimé"
    NOT_FOUND_MSG: ClassVar[str] = "Aucun objet correspondant à supprimer"

    async def perform_deletion(self, instance: ModelT) -> bool:
        await instance.adelete()
        messages.add_message(
            request=self.request,
            level=messages.SUCCESS,
            message=self.DELETION_SUCCESS_MSG.format(instance=instance),
            extra_tags="success",
        )
        return True

    async def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        model_cls = self.get_model_class()
        try:
            instance = await model_cls.objects.aget(pk=pk)
        except model_cls.DoesNotExist:
            messages.add_message(
                request=request,
                level=messages.ERROR,
                message=self.NOT_FOUND_MSG,
                extra_tags="error",
            )
            return HttpResponseRedirect(redirect_to="/")
        await self.perform_deletion(instance)
        return HttpResponseRedirect(redirect_to=request.GET.get("next", "/"))


class BaseFortunesFormView[ModelT: Model](BaseFortunesView):

    template: ClassVar[str]

    @abstractmethod
    async def get_form_class(self) -> type["AbstractForm[ModelT]"]: ...

    async def get_queryset(self) -> "QuerySet[ModelT]":
        return (await self.get_form_class()).get_model().objects.all()  # type: ignore[attr-defined]

    @abstractmethod
    def get_redirect_path(self, instance: ModelT) -> str: ...


class BaseCreateFormView[ModelT: Model](BaseFortunesFormView):

    def handle_integrity_error(self, err: IntegrityError) -> tuple[str, str]:
        return NON_FIELD_ERRORS, f"Database integrity error: {err}"

    async def get(self, request: HttpRequest) -> HttpResponse:
        form_cls, context = await asyncio.gather(
            self.get_form_class(),
            self.get_context_data(),
        )
        return render(
            request=request,
            template_name=self.template,
            context=context | {"form": form_cls()},
        )

    async def post(self, request: HttpRequest) -> HttpResponse:
        form_cls, context = await asyncio.gather(
            self.get_form_class(),
            self.get_context_data(),
        )
        form = form_cls(data=request.POST)
        if form.is_valid():
            try:
                instance = await form.create()
            except IntegrityError as err:
                error_field, validation_error = self.handle_integrity_error(err)
                form.add_error(field=error_field, error=validation_error)
            else:
                return HttpResponseRedirect(self.get_redirect_path(instance))
        return render(
            request=request,
            template_name=self.template,
            context=context | {"form": form},
            status=HTTPStatus.BAD_REQUEST,
        )


class BaseEditFormView[ModelT: Model](BaseFortunesFormView):

    async def get_instance(self, pk: int) -> ModelT:
        queryset = await self.get_queryset()
        return await aget_object_or_404(queryset, pk=pk)

    async def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        form_cls, context = await asyncio.gather(
            self.get_form_class(),
            self.get_context_data(),
        )
        instance = await self.get_instance(pk)
        form = form_cls.from_instance(instance)
        return render(
            request=request,
            template_name=self.template,
            # FIXME is instance necessary
            context=context | {"form": form, "instance": instance},
        )

    async def post(self, request: HttpRequest, pk: int):
        form_cls, context, instance = await asyncio.gather(
            self.get_form_class(), self.get_context_data(), self.get_instance(pk)
        )
        form = form_cls(request.POST)
        if form.is_valid():
            if await form.update(instance):
                messages.add_message(
                    request=request,
                    level=messages.SUCCESS,
                    message=f"{instance._meta.model_name} modifié",
                    extra_tags="success",
                )
            else:
                messages.add_message(
                    request=request,
                    level=messages.INFO,
                    message="Aucune modification",
                    extra_tags="info",
                )
        else:
            return render(
                request=request,
                template_name=self.template,
                # FIXME is instance necessary
                context=context | {"form": form, "instance": instance},
                status=HTTPStatus.BAD_REQUEST,
            )
        return HttpResponseRedirect(self.get_redirect_path(instance))
