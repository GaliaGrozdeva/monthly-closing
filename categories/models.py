from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField("Име", max_length=80, unique=True)
    description = models.TextField("Описание", max_length=1000, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("categories:detail", args=[self.pk])
