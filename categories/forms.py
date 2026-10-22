from django import forms

from .models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        labels = {"name": "Име на категорията", "description": "Кратко описание"}
        help_texts = {
            "name": "До 80 знака. Избери име, което лесно ще разпознаваш.",
            "description": "По желание. Опиши какви инструкции ще събираш тук. До 1000 знака.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Например: Банка", "autofocus": True}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Например: Проверки на банковите движения и свързаните документи."}),
        }
        error_messages = {
            "name": {
                "required": "Въведи име на категорията.",
                "max_length": "Името може да съдържа най-много 80 знака.",
                "unique": "Вече има категория с това име.",
            },
            "description": {"max_length": "Описанието може да съдържа най-много 1000 знака."},
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        # casefold работи и с български букви при SQLite.
        existing_names = Category.objects.exclude(pk=self.instance.pk).values_list("name", flat=True)
        if any(existing.casefold() == name.casefold() for existing in existing_names):
            raise forms.ValidationError("Вече има категория с това име.")
        return name


class CategoryDeleteForm(forms.Form):
    name = forms.CharField(label="Категория за изтриване", disabled=True)
    confirm = forms.BooleanField(
        label="Потвърждавам изтриването на тази категория.",
        error_messages={"required": "Отбележи потвърждението, за да изтриеш категорията."},
    )
