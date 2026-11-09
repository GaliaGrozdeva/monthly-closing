from urllib.parse import parse_qs

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from categories.models import Category
from tags.models import Tag
from .models import Procedure


class ProcedureSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bank = Category.objects.create(name="Банка")
        cls.payroll = Category.objects.create(name="Заплати")
        cls.monthly = Tag.objects.create(name="Месечно")
        cls.check = Tag.objects.create(name="Проверка")
        cls.statement = Procedure.objects.create(category=cls.bank, title="банково извлечение", steps="Проверка на салдото и банковата сметка.")
        cls.advance = Procedure.objects.create(category=cls.bank, title="Аванси", steps="Непогасени плащания.")
        cls.salary = Procedure.objects.create(category=cls.payroll, title="Заплати", steps="Проверка на банковата сметка.")
        cls.archive = Procedure.objects.create(category=cls.bank, title="Януарска проверка", steps="Архив за месеца.")
        cls.statement.tags.add(cls.monthly, cls.check)
        cls.advance.tags.add(cls.monthly)
        cls.salary.tags.add(cls.check)
        cls.url = reverse("procedures:list")

    def results(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return response, list(response.context["procedures"])

    def test_cyrillic_search_in_title_and_steps_with_multiple_words(self):
        for query, expected in [
            ("  БАНКОВАТА   СМЕТКА  ", [self.statement, self.salary]),
            ("САЛДОТО ИЗВЛЕЧЕНИЕ", [self.statement]),
            ("арХив", [self.archive]),
            ("  ", [self.advance, self.statement, self.salary, self.archive]),
        ]:
            with self.subTest(query=query):
                _, found = self.results(q=query)
                self.assertEqual(found, expected)

    def test_category_and_tag_filters_work_together_without_duplicates(self):
        response, found = self.results(q="СМЕТКА", category=self.bank.pk, tag=self.check.pk)
        self.assertEqual(found, [self.statement])
        self.assertEqual(response.context["total_count"], 4)
        self.assertEqual(response.context["selected_category"], self.bank)
        _, found = self.results(tag=self.monthly.pk)
        self.assertEqual(found, [self.advance, self.statement])
        _, found = self.results(category=self.payroll.pk, tag=self.monthly.pk)
        self.assertEqual(found, [])
        _, found = self.results(category=self.bank.pk)
        self.assertEqual(found, [self.advance, self.statement, self.archive])

    def test_supported_sort_orders(self):
        orders = {
            "title": [self.advance, self.statement, self.salary, self.archive],
            "title_desc": [self.archive, self.salary, self.statement, self.advance],
            "category": [self.advance, self.statement, self.archive, self.salary],
            "newest": [self.archive, self.salary, self.advance, self.statement],
        }
        for sort, expected in orders.items():
            with self.subTest(sort=sort):
                _, found = self.results(sort=sort)
                self.assertEqual(found, expected)

    def test_invalid_filters_show_errors_and_escape_search_text(self):
        for params in [
            {"category": "invalid"}, {"category": 99999}, {"category": "9" * 100},
            {"tag": "invalid"}, {"tag": 99999}, {"tag": "9" * 100},
            {"sort": "title; DROP TABLE procedures_procedure"},
            {"q": "Б" * 101},
        ]:
            with self.subTest(params=params):
                response, found = self.results(**params)
                self.assertTrue(response.context["filter_form"].errors)
                self.assertEqual(found, [])
                self.assertContains(response, "Провери филтрите")
        response, found = self.results(q='<script>alert("x")</script>')
        self.assertEqual(found, [])
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertContains(response, "&lt;script&gt;")
        self.assertEqual(Procedure.objects.count(), 4)

    def test_details_keep_validated_search_context(self):
        params = {"q": "БАНКОВАТА сметка", "category": self.bank.pk, "tag": self.check.pk, "sort": "title_desc"}
        response, _ = self.results(**params)
        query = response.context["filter_query"]
        self.assertEqual(parse_qs(query), {key: [str(value)] for key, value in params.items()})
        self.assertContains(response, escape(self.statement.get_absolute_url() + "?" + query))
        detail = self.client.get(self.statement.get_absolute_url(), params)
        self.assertContains(detail, "Към резултатите")
        self.assertContains(detail, escape(self.url + "?" + query))
        self.assertEqual(detail.context["filter_query"], query)
        direct = self.client.get(self.statement.get_absolute_url())
        self.assertEqual(direct.context["filter_query"], "")
        response = self.client.get(self.statement.get_absolute_url(), {"sort": "title", "next": "https://example.invalid/"})
        self.assertNotContains(response, "example.invalid")
        self.assertEqual(response.context["filter_query"], "sort=title")

    def test_no_matches_is_different_from_empty_library(self):
        response, found = self.results(q="НЕСЪЩЕСТВУВАЩА ДУМА")
        self.assertEqual(found, [])
        self.assertContains(response, "Няма съвпадения")
        self.assertNotContains(response, "Все още няма процедури")
        Procedure.objects.all().delete()
        response, found = self.results()
        self.assertContains(response, "Все още няма процедури")
        self.assertEqual(found, [])
        self.assertEqual(response.context["total_count"], 0)

    def test_new_procedure_uses_selected_category(self):
        response, _ = self.results(category=self.bank.pk)
        create_url = reverse("procedures:create") + "?category=" + str(self.bank.pk)
        self.assertContains(response, create_url)
        self.assertContains(response, 'aria-keyshortcuts="F3"')
        self.assertContains(response, 'aria-keyshortcuts="Escape"')
        create = self.client.get(create_url)
        self.assertEqual(create.context["form"]["category"].value(), self.bank.pk)
