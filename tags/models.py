from django.db import models
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField("Име", max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Етикет"
        verbose_name_plural = "Етикети"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("tags:detail", args=[self.pk])
