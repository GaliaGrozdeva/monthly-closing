from django.test import Client, TestCase, override_settings
from django.urls import reverse

from categories.models import Category
from .models import Procedure


class ProcedureWorkflowTests(TestCase):
    def setUp(self):
        self.bank = Category.objects.create(name="БАНКА", description="Съществуваща инструкция.")
        self.payroll = Category.objects.create(name="Заплати")
        self.create_url = reverse("procedures:create")

    def data(self, **changes):
        return {"category": self.bank.pk, "title": "Обработка на извлечение", "steps": "1. Провери периода.\n2. Обработи извлечението.", **changes}

    def test_create_read_and_move_between_categories(self):
        response = self.client.get(self.create_url, {"category": self.bank.pk})
        self.assertEqual(response.context["form"]["category"].value(), self.bank.pk)
        response = self.client.post(self.create_url, self.data())
        procedure = Procedure.objects.get()
        self.assertRedirects(response, procedure.get_absolute_url())
        self.assertContains(self.client.get(self.bank.get_absolute_url()), procedure.title)
        self.assertContains(self.client.get(reverse("procedures:list")), procedure.title)
        self.assertContains(self.client.get(procedure.get_absolute_url()), "Провери периода.")
        response = self.client.post(reverse("procedures:edit", args=[procedure.pk]), self.data(category=self.payroll.pk, steps="Обновена инструкция."))
        self.assertRedirects(response, procedure.get_absolute_url())
        procedure.refresh_from_db()
        self.assertEqual(procedure.category, self.payroll)
        self.assertEqual(procedure.steps, "Обновена инструкция.")
        self.assertNotContains(self.client.get(self.bank.get_absolute_url()), procedure.title)
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.description, "Съществуваща инструкция.")

    def test_validation_and_bulgarian_duplicate_titles(self):
        for changes in [{"title": "   "}, {"steps": "   "}, {"category": ""}, {"category": 999}, {"title": "Б" * 121}, {"steps": "Б" * 6001}]:
            response = self.client.post(self.create_url, self.data(**changes))
            self.assertTrue(response.context["form"].errors)
        self.assertEqual(Procedure.objects.count(), 0)
        self.client.post(self.create_url, self.data())
        response = self.client.post(self.create_url, self.data(title=" ОБРАБОТКА НА ИЗВЛЕЧЕНИЕ "))
        self.assertContains(response, "В тази категория вече има процедура с това заглавие.")
        self.assertEqual(Procedure.objects.count(), 1)
        self.client.post(self.create_url, self.data(category=self.payroll.pk))
        self.assertEqual(Procedure.objects.count(), 2)

    def test_category_cannot_be_deleted_until_procedure_is_moved(self):
        procedure = Procedure.objects.create(category=self.bank, title="Проверка", steps="Провери извлечението.")
        url = reverse("categories:delete", args=[self.bank.pk])
        response = self.client.post(url, {"confirm": "on"})
        self.assertContains(response, "Категорията съдържа процедури.")
        self.assertTrue(Category.objects.filter(pk=self.bank.pk).exists())
        self.assertTrue(Procedure.objects.filter(pk=procedure.pk).exists())
        self.client.post(reverse("procedures:edit", args=[procedure.pk]), self.data(category=self.payroll.pk))
        self.assertRedirects(self.client.post(url, {"confirm": "on"}), reverse("categories:list"))
        self.assertTrue(Procedure.objects.filter(pk=procedure.pk, category=self.payroll).exists())

    def test_procedure_deletion_requires_confirmation_and_preserves_category(self):
        procedure = Procedure.objects.create(category=self.bank, title="Проверка", steps="Провери.")
        other = Procedure.objects.create(category=self.bank, title="Друга проверка", steps="Провери отново.")
        url = reverse("procedures:delete", args=[procedure.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url, {})
        self.assertTrue(Procedure.objects.filter(pk=procedure.pk).exists())
        self.assertEqual(self.client.delete(url).status_code, 405)
        response = self.client.post(url, {"confirm": "on", "title": other.title})
        self.assertRedirects(response, self.bank.get_absolute_url())
        self.assertFalse(Procedure.objects.filter(pk=procedure.pk).exists())
        self.assertTrue(Procedure.objects.filter(pk=other.pk).exists())
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.description, "Съществуваща инструкция.")

    def test_empty_library_guides_user_to_create_category(self):
        Category.objects.all().delete()
        self.assertContains(self.client.get(self.create_url), "Първо създай категория")
        self.assertContains(self.client.get(reverse("procedures:list")), "Все още няма процедури")
        self.client.post(self.create_url, self.data())
        self.assertEqual(Procedure.objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_missing_records_csrf_and_safe_instruction_display(self):
        for page in ["detail", "edit", "delete"]:
            self.assertEqual(self.client.get(reverse("procedures:" + page, args=[999])).status_code, 404)
        for category in ["invalid", "999"]:
            self.assertEqual(self.client.get(self.create_url, {"category": category}).status_code, 404)
        response = Client(enforce_csrf_checks=True).post(self.create_url, self.data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Procedure.objects.count(), 0)
        procedure = Procedure.objects.create(category=self.bank, title="Проверка", steps="<script>alert('test')</script>\nВтори ред.")
        response = self.client.get(procedure.get_absolute_url())
        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")
        self.assertContains(response, "Втори ред.")
