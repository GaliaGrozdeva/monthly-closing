from django import forms

from .models import Procedure


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = Procedure
        fields = ["category", "title", "steps"]
        labels = {"category": "Категория", "title": "Заглавие на процедурата", "steps": "Инструкция — стъпка по стъпка"}
        help_texts = {
            "category": "Избери темата, към която принадлежи инструкцията.",
            "title": "До 120 знака. Например: Обработка на банково извлечение.",
            "steps": "Опиши последователността с обикновен текст. Можеш да номерираш стъпките. До 6000 знака.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например: Обработка на банково извлечение"}),
            "steps": forms.Textarea(attrs={"rows": 10, "placeholder": "1. Получи извлечението.\n2. Провери периода.\n3. ..."}),
        }
        error_messages = {
            "category": {"required": "Избери категория.", "invalid_choice": "Избери съществуваща категория."},
            "title": {"required": "Въведи заглавие.", "max_length": "Заглавието може да съдържа най-много 120 знака."},
            "steps": {"required": "Въведи инструкцията.", "max_length": "Инструкцията може да съдържа най-много 6000 знака."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "Избери категория"

    def clean(self):
        cleaned = super().clean()
        category, title = cleaned.get("category"), cleaned.get("title")
        if category and title:
            titles = Procedure.objects.filter(category=category).exclude(pk=self.instance.pk).values_list("title", flat=True)
            if any(existing.casefold() == title.casefold() for existing in titles):
                self.add_error("title", "В тази категория вече има процедура с това заглавие.")
        return cleaned


class ProcedureDeleteForm(forms.Form):
    title = forms.CharField(label="Процедура за изтриване", disabled=True)
    confirm = forms.BooleanField(
        label="Потвърждавам изтриването на тази процедура.",
        error_messages={"required": "Отбележи потвърждението, за да изтриеш процедурата."},
    )
