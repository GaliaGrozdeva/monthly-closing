from django.template import Context, Template
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from categories.models import Category
from tags.models import Tag
from .models import Procedure
from .templatetags.procedure_extras import count_steps


class CountStepsTests(SimpleTestCase):
    def test_numbered_steps_with_intro_and_continuation_lines(self):
        text = "Общи правила за банката.\n\n1. Получи извлечението.\nУточни периода.\n\n2. Провери салдото."
        self.assertEqual(count_steps(text), 2)

    def test_windows_lines_parentheses_and_indentation(self):
        text = "1) Получи документите.\r\n\r\n  2) Подреди ги.\r\n\t10. Провери отчета."
        self.assertEqual(count_steps(text), 3)

    def test_dates_substeps_and_empty_markers_are_not_steps(self):
        text = "10.11.2026\n1.1 Подточка\n- Забележка\n1.\n2)   \n3.Без интервал\nВиж 4. по-долу."
        for value in [text, "Свободен текст.", "", " \n\t", None, 42]:
            with self.subTest(value=value):
                self.assertEqual(count_steps(value), 0)

    def test_filter_is_registered_and_loads_in_a_template(self):
        template = Template("{% load procedure_extras %}{{ steps|count_steps }}")
        self.assertEqual(template.render(Context({"steps": "1. Провери.\n2. Сравни."})), "2")


class StepCountPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Банкови извлечения")
        cls.tag = Tag.objects.create(name="Проверка")
        cls.procedure = Procedure.objects.create(
            category=cls.category, title="Обработка на извлечение",
            steps="Общи правила.\n1. Получи извлечението.\n\n2. <script>alert('test')</script>",
        )
        cls.procedure.tags.add(cls.tag)

    def page_urls(self):
        return [
            reverse("procedures:list"), self.procedure.get_absolute_url(),
            self.category.get_absolute_url(), self.tag.get_absolute_url(),
        ]

    def test_count_is_shown_on_all_procedure_pages_and_text_is_escaped(self):
        for url in self.page_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "2 стъпки", count=1)
                self.assertNotContains(response, "<script>")
                self.assertContains(response, "&lt;script&gt;")

    def test_count_updates_after_edit_and_is_hidden_for_unnumbered_text(self):
        for text, expected in [("1) Единствена проверка.", "1 стъпка"), ("Свободен текст.", None)]:
            response = self.client.post(reverse("procedures:edit", args=[self.procedure.pk]), {
                "category": self.category.pk, "title": self.procedure.title,
                "steps": text, "tags": [self.tag.pk],
            })
            self.assertRedirects(response, self.procedure.get_absolute_url())
            for url in self.page_urls():
                with self.subTest(url=url, text=text):
                    response = self.client.get(url)
                    if expected:
                        self.assertContains(response, expected, count=1)
                    else:
                        self.assertNotContains(response, 'class="step-count"')
                        self.assertContains(response, text)
