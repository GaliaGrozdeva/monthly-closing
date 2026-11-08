from django import forms

from .models import Tag


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
        labels = {"name": "Име на етикета"}
        help_texts = {"name": "До 50 знака. Кратка дума или израз, например Месечно или Проверка."}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Например: Месечно", "autofocus": True}),
        }
        error_messages = {
            "name": {
                "required": "Въведи име на етикета.",
                "max_length": "Името може да съдържа най-много 50 знака.",
                "unique": "Вече има етикет с това име.",
            },
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        existing_names = Tag.objects.exclude(pk=self.instance.pk).values_list("name", flat=True)
        if any(existing.casefold() == name.casefold() for existing in existing_names):
            raise forms.ValidationError("Вече има етикет с това име.")
        return name


class TagDeleteForm(forms.Form):
    name = forms.CharField(label="Етикет за изтриване", disabled=True)
    confirm = forms.BooleanField(
        label="Потвърждавам изтриването на този етикет.",
        error_messages={"required": "Отбележи потвърждението, за да изтриеш етикета."},
    )
