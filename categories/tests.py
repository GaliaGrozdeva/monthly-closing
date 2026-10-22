from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Category


class CategoryWorkflowTests(TestCase):
    def test_empty_database_pages_and_create(self):
        for page in ["home", "about", "categories:list", "categories:create"]:
            self.assertEqual(self.client.get(reverse(page)).status_code, 200)
        response = self.client.post(reverse("categories:create"), {
            "name": "Банка", "description": "Проверка на банковите движения.",
        })
        category = Category.objects.get(name="Банка")
        self.assertRedirects(response, category.get_absolute_url())
        self.assertContains(self.client.get(category.get_absolute_url()), "Проверка на банковите движения.")

    def test_invalid_input_does_not_create_categories(self):
        for name in ["", "   ", "Б" * 81]:
            response = self.client.post(reverse("categories:create"), {"name": name})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertEqual(Category.objects.count(), 0)
        response = self.client.post(reverse("categories:create"), {"name": "Банка", "description": "а" * 1001})
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Category.objects.count(), 0)

    def test_duplicate_bulgarian_name_and_whitespace(self):
        Category.objects.create(name="Банка")
        response = self.client.post(reverse("categories:create"), {"name": "  БАНКА  "})
        self.assertContains(response, "Вече има категория с това име.")
        self.assertEqual(Category.objects.count(), 1)

    def test_edit_allows_own_name_and_rejects_another_category_name(self):
        category = Category.objects.create(name="Банка")
        other = Category.objects.create(name="Заплати")
        url = reverse("categories:edit", args=[category.pk])
        response = self.client.post(url, {"name": "Банка", "description": "Обновено описание"})
        self.assertRedirects(response, category.get_absolute_url())
        category.refresh_from_db()
        self.assertEqual(category.description, "Обновено описание")
        response = self.client.post(url, {"name": other.name})
        self.assertTrue(response.context["form"].errors)
        category.refresh_from_db()
        self.assertEqual(category.name, "Банка")

    def test_deletion_requires_post_confirmation_and_keeps_other_records(self):
        category = Category.objects.create(name="Банка")
        other = Category.objects.create(name="Заплати")
        url = reverse("categories:delete", args=[category.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(Category.objects.count(), 2)
        response = self.client.post(url, {})
        self.assertTrue(response.context["form"].errors)
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())
        # Подменено disabled поле не променя целта на изтриването.
        response = self.client.post(url, {"confirm": "on", "name": other.name})
        self.assertRedirects(response, reverse("categories:list"))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
        self.assertTrue(Category.objects.filter(pk=other.pk).exists())

    def test_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("categories:create"), {"name": "Банка"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Category.objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_missing_pages_show_custom_404(self):
        for url in ["/not-a-page/", reverse("categories:detail", args=[999])]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            self.assertContains(response, "Тази страница не е намерена", status_code=404)

    def test_user_text_is_escaped(self):
        category = Category.objects.create(name="Банка", description="<script>alert('x')</script>")
        response = self.client.get(category.get_absolute_url())
        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_unsupported_methods_do_not_change_data(self):
        category = Category.objects.create(name="Банка")
        response = self.client.delete(reverse("categories:delete", args=[category.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())
