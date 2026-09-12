from datetime import date
from typing import Any
from django import forms

from fortunes.app.forms.base import AbstractForm, FortuneDateInput
from fortunes.app.models import Author, Fortune


class BaseFortuneForm(AbstractForm[Fortune]):

    date = forms.DateField(
        label="Date",
        widget=FortuneDateInput(format="%Y-%m-%d"),
        initial=date.today().isoformat(),
        required=False,
    )
    text = forms.CharField(
        label="Fortune",
        strip=True,
        widget=forms.Textarea(),
    )
    hidden = forms.BooleanField(
        label="Caché",
        required=False,
        initial=False,
    )

    def clean(self) -> dict[str, Any] | None:
        cleaned_data = super().clean()
        if not cleaned_data:
            return None
        if raw_author_id := cleaned_data.get("author_id"):
            cleaned_data["author_id"] = int(raw_author_id)
        return cleaned_data


async def build_fortune_form_cls() -> type[BaseFortuneForm]:
    authors = [i async for i in Author.objects.values_list("id", "name")]
    return type(
        "FortuneForm",
        (BaseFortuneForm,),
        {
            "author_id": forms.ChoiceField(
                choices=authors,
                label="Auteur",
            )
        },
    )
