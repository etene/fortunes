from typing import Self, get_args
from django import forms
from django.db.models import Model


class FortuneDateInput(forms.DateInput):
    input_type = "date"


class AbstractForm[ModelT: Model](forms.Form):

    @classmethod
    def get_model(cls) -> type[ModelT]:
        return get_args(cls.__orig_bases__[0])[0]  # type: ignore[attr-defined]

    async def create(self) -> ModelT:
        """Create a new instance with the form's validated data."""
        assert self.is_valid()
        return await self.get_model().objects.acreate(**self.cleaned_data)  # type: ignore[attr-defined]

    async def update(self, instance: ModelT):
        """Update an instance with the form's validated data."""
        assert self.is_valid()
        if self.changed_data:
            for field in self.changed_data:
                setattr(instance, field, self.cleaned_data[field])
            await instance.asave(update_fields=self.changed_data)

    @classmethod
    def from_instance(cls, instance: ModelT) -> Self:
        return cls(data={i: getattr(instance, i) for i in cls.declared_fields})
