from datetime import date
from typing import Any
from django import forms

from fortunes.app.models import Author


class FortuneDateInput(forms.DateInput):
    input_type = "date"


async def build_fortune_form(
    data: dict[str, Any] | None = None,
) -> forms.Form:
    authors = [i async for i in Author.objects.values_list("id", "name")]

    class FortuneForm(forms.Form):
        fortune_author_id = forms.ChoiceField(
            choices=authors,
            label="Auteur",
        )
        fortune_date = forms.DateField(
            label="Date",
            widget=FortuneDateInput(format="%Y-%m-%d"),
            initial=date.today().isoformat(),
        )
        fortune_text = forms.CharField(
            label="Fortune",
            strip=True,
            widget=forms.Textarea(),
        )
        fortune_hidden = forms.BooleanField(
            label="Caché",
            required=False,
            initial=False,
        )

    return FortuneForm(data=data)
