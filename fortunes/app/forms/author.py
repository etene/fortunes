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
    async def guess_immich_info(cls, author: Author) -> bool:
        if author.name and author.immich_id and author.birthday:
            return False
        try:
            immich_person = await immich.find_person(name=author.name)
        except LookupError:
            # TODO log ?
            return False
        changed: set[str] = set()
        if not author.immich_id:
            author.immich_id = immich_person.id
            changed.add("immich_id")
        if not author.birthday:
            author.birthday = immich_person.birth_date
            changed.add("birthday")
        if changed:
            await author.asave(update_fields=changed)
            return True
        return False

    async def create(self) -> Author:
        created = await super().create()
        await self.guess_immich_info(created)
        return created

    async def update(self, instance: Author) -> bool:
        updated = await super().update(instance)
        immich_info_updated = await self.guess_immich_info(instance)
        return updated or immich_info_updated
