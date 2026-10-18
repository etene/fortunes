from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import aget_object_or_404, render
from django.views.generic import View
import asyncio
from http import HTTPStatus
from fortunes.app.models import Author

if TYPE_CHECKING:
    from fortunes.app.forms.base import AbstractForm
    from django.db.models import Model, QuerySet


class BaseFortunesView(View):

    async def get_context_data(self) -> dict[str, Any]:
        return {"authors": [i async for i in Author.objects.all()]}


class BaseFortunesFormView[ModelT: Model](ABC, BaseFortunesView):

    template: ClassVar[str]

    @abstractmethod
    async def get_form_class(self) -> type["AbstractForm[ModelT]"]: ...

    async def get_queryset(self) -> "QuerySet[ModelT]":
        return (await self.get_form_class()).get_model().objects.all()  # type: ignore[attr-defined]

    @abstractmethod
    def get_redirect_path(self, instance: ModelT) -> str: ...


class BaseCreateFormView[ModelT: Model](BaseFortunesFormView):

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
            instance = await form.create()
            return HttpResponseRedirect(self.get_redirect_path(instance))
        else:
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
                    message=f"{instance._meta.model_name} updated successfully",
                    extra_tags="info",
                )
            else:
                messages.add_message(
                    request=request,
                    level=messages.INFO,
                    message="No changes",
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
