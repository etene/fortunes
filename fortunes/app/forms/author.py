from django import forms

from fortunes import immich
from fortunes.app.forms.base import AbstractForm, FortuneDateInput
from fortunes.app.models import Author


class AuthorForm(AbstractForm[Author]):
    name = forms.CharField(
        label="Nom",
        strip=True,
    )
    birthday = forms.DateField(
        label="Date de naissance",
        widget=FortuneDateInput(format="%Y-%m-%d"),
        required=False,
    )
    immich_id = forms.UUIDField(
        label="ID utilisateur Immich",
        required=False,
        widget=forms.widgets.TextInput(
            attrs={"style": "font-family:monospace;"},
        ),
    )

    @classmethod
    async def guess_immich_id(cls, author: Author) -> None:
        try:
            author.immich_id = await immich.find_person_id(name=author.name)
        except LookupError:
            # TODO log ?
            pass
        else:
            await author.asave()

    async def create(self) -> Author:
        created = await super().create()
        if not created.immich_id:
            await self.guess_immich_id(created)
        return created

    async def update(self, instance: Author) -> bool:
        old_immich_id = instance.immich_id
        if not await super().update(instance):
            return False
        if old_immich_id != instance.immich_id:
            await self.guess_immich_id(instance)
        return True
