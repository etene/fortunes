from http import HTTPMethod, HTTPStatus
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import aget_object_or_404, render
from random import randint
from datetime import UTC, date, datetime
from fortunes.app.forms import build_fortune_form
from fortunes.immich import get_random_image
from .models import Author, Fortune


async def random_fortune(request):
    non_hidden_fortunes = Fortune.objects.exclude(hidden=True).with_authors()
    fortune_count = await non_hidden_fortunes.acount()
    random_fortune_offset = randint(0, fortune_count - 1)
    random_fortune = await non_hidden_fortunes[
        random_fortune_offset : random_fortune_offset + 1
    ].aget()
    context = {"fortune": random_fortune, "display_images": True}
    return render(request, "app/index.html", context)


async def random_image(request, fortune_id: int):
    try:
        fortune = await Fortune.objects.with_authors().aget(pk=fortune_id)
    except Fortune.DoesNotExist:
        return HttpResponseNotFound()
    image_bytes = await get_random_image(
        taken_after=datetime(year=fortune.date.year, month=1, day=1, tzinfo=UTC),
        taken_before=datetime(year=fortune.date.year + 1, month=1, day=1, tzinfo=UTC),
        with_person=fortune.author,
        search_term="portrait",
    )
    return HttpResponse(
        content=image_bytes,
        headers={"content-type": "image/jpg"},
    )


async def single_fortune(request, fortune_id: int):
    fortune = await aget_object_or_404(Fortune.objects.with_authors(), pk=fortune_id)
    context = {"fortune": fortune, "display_images": True}
    return render(request, "app/detail.html", context)


async def fortune_list(request):
    context = {
        "fortunes": [
            i async for i in Fortune.objects.with_authors().order_by("-date").all()[:10]
        ]
    }
    return render(request, "app/fortune_list.html", context)


async def new_fortune(request):
    authors = [i async for i in Author.objects.all()]
    if request.method == HTTPMethod.GET:
        context = {
            "authors": authors,
            "selected_author": authors[0] if authors else None,
            "fortune_date": date.today().isoformat(),
            "form": await build_fortune_form(),
        }
        return render(request, "app/new_fortune.html", context)
    elif request.method == HTTPMethod.POST:
        form = await build_fortune_form(data=request.POST)
        if form.is_valid():
            created_fortune = await Fortune.objects.acreate(
                author_id=int(form.cleaned_data["fortune_author_id"]),
                date=form.cleaned_data["fortune_date"],
                text=form.cleaned_data["fortune_text"],
                hidden=form.cleaned_data["fortune_hidden"],
            )
            return HttpResponseRedirect(f"/{created_fortune.id}/")
        context = {
            "authors": authors,
            "selected_author": authors[0] if authors else None,
            "fortune_date": date.today().isoformat(),
            "form": form,
            "form_target": "/new/",
        }
        return render(
            request=request,
            template_name="app/edit_fortune.html",
            context=context,
            status=HTTPStatus.BAD_REQUEST,
        )


async def edit_fortune(request, fortune_id: int):
    fortune = await aget_object_or_404(Fortune.objects.with_authors(), pk=fortune_id)
    context = {"fortune": fortune, "display_images": True}
    status = HTTPStatus.OK
    if request.method == HTTPMethod.POST:
        form = await build_fortune_form(request.POST)
        if form.is_valid():
            for field in form.changed_data:
                setattr(
                    fortune, field.removeprefix("fortune_"), form.cleaned_data[field]
                )
            if form.changed_data:
                await fortune.asave()
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
