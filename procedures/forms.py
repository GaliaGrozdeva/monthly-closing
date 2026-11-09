from urllib.parse import urlencode

from django import forms

from categories.models import Category
from tags.models import Tag
from .models import Procedure


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = Procedure
        fields = ["category", "title", "tags", "steps"]
        labels = {"category": "Категория", "title": "Заглавие на процедурата", "steps": "Инструкция — стъпка по стъпка", "tags": "Етикети"}
        help_texts = {
            "category": "Избери темата, към която принадлежи инструкцията.",
            "title": "До 120 знака. Например: Обработка на банково извлечение.",
            "tags": "По желание. Избери един или няколко етикета с отметки.",
            "steps": "Опиши последователността с обикновен текст. Можеш да номерираш стъпките. До 6000 знака.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например: Обработка на банково извлечение", "autofocus": True}),
            "tags": forms.CheckboxSelectMultiple(attrs={"class": "tag-choices"}),
            "steps": forms.Textarea(attrs={"rows": 10, "placeholder": "1. Получи извлечението.\n2. Провери периода.\n3. ..."}),
        }
        error_messages = {
            "tags": {"invalid_choice": "Избери съществуващи етикети.", "invalid_pk_value": "Избери съществуващи етикети.", "invalid_list": "Избери етикетите от списъка."},
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

class ProcedureFilterForm(forms.Form):
    q = forms.CharField(
        label="Търсене", required=False, max_length=100,
        widget=forms.TextInput(attrs={
            "placeholder": "Например: банкова сметка",
            "autofocus": True, "data-shortcut": "search", "aria-keyshortcuts": "F3",
        }),
        error_messages={"max_length": "Търсенето може да съдържа най-много 100 знака."},
    )
    category = forms.ModelChoiceField(
        label="Категория", queryset=Category.objects.all(), required=False,
        empty_label="Всички категории",
        error_messages={"invalid_choice": "Избери съществуваща категория или всички категории."},
    )
    tag = forms.ModelChoiceField(
        label="Етикет", queryset=Tag.objects.all(), required=False,
        empty_label="Всички етикети",
        error_messages={"invalid_choice": "Избери съществуващ етикет или всички етикети."},
    )
    sort = forms.ChoiceField(
        label="Подреждане", required=False,
        choices=[
            ("title", "Заглавие: А–Я"),
            ("title_desc", "Заглавие: Я–А"),
            ("category", "По категория"),
            ("newest", "Последно добавени"),
        ],
        error_messages={"invalid_choice": "Избери подреждане от списъка."},
    )

    def clean_sort(self):
        return self.cleaned_data["sort"] or "title"

    def get_query_string(self):
        if not self.is_valid():
            return ""
        data = self.cleaned_data
        values = {
            "q": data["q"],
            "category": data["category"].pk if data["category"] else "",
            "tag": data["tag"].pk if data["tag"] else "",
            "sort": data["sort"],
        }
        return urlencode({key: value for key, value in values.items() if value})
