from django import forms

from fortunes.app.forms.base import AbstractForm, FortuneDateInput
from fortunes.app.models import Author


class AuthorForm(AbstractForm[Author]):
    name = forms.CharField(
        label="Nom",
        strip=True,
    )
    birthday = forms.DateTimeField(
        label="Date de naissance",
        widget=FortuneDateInput(format="%Y-%m-%d"),
        required=False,
    )
    immich_id = forms.UUIDField(
        label="ID utilisateur Iimmich",
        required=False,
    )
