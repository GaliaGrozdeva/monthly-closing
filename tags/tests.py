from django.test import Client, TestCase, override_settings
from django.urls import reverse

from categories.models import Category
from procedures.models import Procedure
from .models import Tag


class TagWorkflowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Банка")

    def procedure_data(self, **changes):
        return {"category": self.category.pk, "title": "Банкова проверка", "steps": "Провери периода.", **changes}

    def test_create_validation_and_rename(self):
        url = reverse("tags:create")
        for name in ["", "   ", "Б" * 51]:
            response = self.client.post(url, {"name": name})
            self.assertTrue(response.context["form"].errors)
        self.assertEqual(Tag.objects.count(), 0)
        response = self.client.post(url, {"name": "  Месечно  "})
        tag = Tag.objects.get()
        self.assertEqual(tag.name, "Месечно")
        self.assertRedirects(response, tag.get_absolute_url())
        response = self.client.post(url, {"name": "МЕСЕЧНО"})
        self.assertContains(response, "Вече има етикет с това име.")
        other = Tag.objects.create(name="Проверка")
        edit_url = reverse("tags:edit", args=[tag.pk])
        self.assertTrue(self.client.post(edit_url, {"name": other.name}).context["form"].errors)
        self.assertRedirects(self.client.post(edit_url, {"name": "Месечно"}), tag.get_absolute_url())
        self.assertRedirects(self.client.post(edit_url, {"name": "Всеки месец"}), tag.get_absolute_url())
        tag.refresh_from_db()
        self.assertEqual(tag.name, "Всеки месец")
        self.assertContains(self.client.get(reverse("tags:list")), tag.name)

    def test_many_to_many_create_replace_clear_and_tag_details(self):
        monthly = Tag.objects.create(name="Месечно")
        check = Tag.objects.create(name="Проверка")
        response = self.client.post(reverse("procedures:create"), self.procedure_data(tags=[monthly.pk, check.pk]))
        procedure = Procedure.objects.get()
        self.assertRedirects(response, procedure.get_absolute_url())
        self.assertSetEqual(set(procedure.tags.all()), {monthly, check})
        other = Procedure.objects.create(category=self.category, title="Друга инструкция", steps="Друг текст.")
        other.tags.add(monthly)
        self.assertContains(self.client.get(monthly.get_absolute_url()), other.title)
        self.assertNotContains(self.client.get(check.get_absolute_url()), other.title)
        edit_url = reverse("procedures:edit", args=[procedure.pk])
        page = self.client.get(edit_url)
        self.assertContains(page, "<fieldset")
        self.assertSetEqual(set(map(int, page.context["form"]["tags"].value())), {monthly.pk, check.pk})
        self.client.post(reverse("tags:edit", args=[monthly.pk]), {"name": "Месечна задача"})
        self.assertContains(self.client.get(procedure.get_absolute_url()), "Месечна задача")
        self.client.post(edit_url, self.procedure_data(tags=[check.pk]))
        self.assertSetEqual(set(procedure.tags.all()), {check})
        self.assertTrue(other.tags.filter(pk=monthly.pk).exists())
        self.client.post(edit_url, self.procedure_data())
        self.assertEqual(procedure.tags.count(), 0)
        self.assertEqual(Tag.objects.count(), 2)

    def test_invalid_tags_do_not_save_changes_or_remove_existing_links(self):
        tag = Tag.objects.create(name="Проверка")
        procedure = Procedure.objects.create(category=self.category, title="Оригинално заглавие", steps="Оригинален текст.")
        procedure.tags.add(tag)
        url = reverse("procedures:edit", args=[procedure.pk])
        for value in ["99999", "invalid"]:
            response = self.client.post(url, self.procedure_data(tags=[value]))
            self.assertContains(response, "Избери съществуващи етикети.")
        procedure.refresh_from_db()
        self.assertEqual(procedure.title, "Оригинално заглавие")
        self.assertEqual(procedure.steps, "Оригинален текст.")
        self.assertSetEqual(set(procedure.tags.all()), {tag})

    def test_delete_requires_confirmation_and_keeps_procedures(self):
        tag = Tag.objects.create(name="Месечно")
        other = Tag.objects.create(name="Проверка")
        procedure = Procedure.objects.create(category=self.category, title="Банкова проверка", steps="Запазен текст.")
        procedure.tags.add(tag, other)
        url = reverse("tags:delete", args=[tag.pk])
        response = self.client.get(url)
        self.assertTrue(response.context["form"].fields["name"].disabled)
        self.client.post(url, {})
        self.assertTrue(Tag.objects.filter(pk=tag.pk).exists())
        self.assertEqual(self.client.delete(url).status_code, 405)
        response = self.client.post(url, {"confirm": "on", "name": other.name})
        self.assertRedirects(response, reverse("tags:list"))
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())
        procedure.refresh_from_db()
        self.assertEqual(procedure.steps, "Запазен текст.")
        self.assertEqual(procedure.category, self.category)
        self.assertSetEqual(set(procedure.tags.all()), {other})

    def test_empty_database_flow_does_not_require_tags(self):
        self.category.delete()
        self.assertContains(self.client.get(reverse("tags:list")), "Все още няма етикети")
        self.client.post(reverse("categories:create"), {"name": "Документи"})
        self.category = Category.objects.get()
        self.assertContains(self.client.get(reverse("procedures:create")), "Все още няма етикети")
        response = self.client.post(reverse("procedures:create"), self.procedure_data())
        procedure = Procedure.objects.get()
        self.assertRedirects(response, procedure.get_absolute_url())
        self.assertEqual(procedure.tags.count(), 0)
        self.client.post(reverse("tags:create"), {"name": "Подготовка"})
        tag = Tag.objects.get()
        self.client.post(reverse("procedures:edit", args=[procedure.pk]), self.procedure_data(tags=[tag.pk]))
        self.assertContains(self.client.get(tag.get_absolute_url()), procedure.title)

    @override_settings(DEBUG=False)
    def test_missing_pages_csrf_and_escaped_names(self):
        for page in ["detail", "edit", "delete"]:
            self.assertEqual(self.client.get(reverse("tags:" + page, args=[999])).status_code, 404)
        response = Client(enforce_csrf_checks=True).post(reverse("tags:create"), {"name": "Проверка"})
        self.assertEqual(response.status_code, 403)
        tag = Tag.objects.create(name="<script>alert('x')</script>")
        for url in [reverse("tags:list"), tag.get_absolute_url()]:
            response = self.client.get(url)
            self.assertNotContains(response, "<script>")
            self.assertContains(response, "&lt;script&gt;")

    def test_keyboard_actions_are_available_for_each_model(self):
        tag = Tag.objects.create(name="Проверка")
        procedure = Procedure.objects.create(category=self.category, title="Банка", steps="Провери.")
        for app, obj in [("categories", self.category), ("procedures", procedure), ("tags", tag)]:
            for page in ["create", "edit"]:
                url = reverse(app + ":" + page, args=[obj.pk] if page == "edit" else [])
                response = self.client.get(url)
                self.assertContains(response, 'aria-keyshortcuts="F1"')
                self.assertContains(response, 'aria-keyshortcuts="F2"')
                self.assertContains(response, 'aria-keyshortcuts="Escape"')
            response = self.client.get(obj.get_absolute_url())
            self.assertContains(response, 'aria-keyshortcuts="Alt+E"')
            self.assertContains(response, 'aria-keyshortcuts="Alt+D"')
            response = self.client.get(reverse(app + ":delete", args=[obj.pk]))
            self.assertNotContains(response, 'data-shortcut="save"')
