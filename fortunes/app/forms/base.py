from typing import Self, get_args
from django import forms
from django.db.models import Model
from logging import getLogger

LOG = getLogger(__name__)


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

    async def update(self, instance: ModelT) -> bool:
        """Update an instance with the form's validated data.

        Return True if the instance was saved, False otherwise.
        """
        assert self.is_valid()
        really_changed_data: set[str] = set()
        if self.has_changed():
            for field in self.changed_data:
                old_value = getattr(instance, field)
                new_value = self.cleaned_data[field]
                if old_value != new_value:
                    LOG.error("%s changed from %r to %r", field, old_value, new_value)
                    setattr(instance, field, new_value)
                    really_changed_data.add(field)
            if really_changed_data:
                await instance.asave(update_fields=really_changed_data)
                return True
        return False

    @classmethod
    def from_instance(cls, instance: ModelT) -> Self:
        return cls(data={i: getattr(instance, i) for i in cls.declared_fields})
