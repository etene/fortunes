from datetime import date
from typing import Any
from django import forms

from fortunes.app.models import Author, Fortune


class FortuneDateInput(forms.DateInput):
    input_type = "date"


class BaseFortuneForm(forms.Form):

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

    async def update_fortune(self, fortune: Fortune):
        """Update a fortune with the form's validated data."""
        assert self.is_valid()
        for field in self.changed_data:
            setattr(fortune, field.removeprefix("fortune_"), self.cleaned_data[field])
        if self.changed_data:
            await fortune.asave()

    async def create_fortune(self) -> Fortune:
        """Create a new fortune with the form's validated data."""
        assert self.is_valid()
        return await Fortune.objects.acreate(
            author_id=int(self.cleaned_data["fortune_author_id"]),
            date=self.cleaned_data["fortune_date"],
            text=self.cleaned_data["fortune_text"],
            hidden=self.cleaned_data["fortune_hidden"],
        )


async def build_fortune_form(
    data: dict[str, Any] | None = None,
) -> BaseFortuneForm:
    authors = [i async for i in Author.objects.values_list("id", "name")]

    class FortuneForm(BaseFortuneForm):
        fortune_author_id = forms.ChoiceField(
            choices=authors,
            label="Auteur",
        )

    return FortuneForm(data=data)
