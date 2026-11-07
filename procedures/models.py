from django.db import models
from django.urls import reverse


class Procedure(models.Model):
    category = models.ForeignKey(
        "categories.Category", on_delete=models.PROTECT,
        related_name="procedures", verbose_name="Категория",
    )
    title = models.CharField("Заглавие", max_length=120)
    steps = models.TextField("Инструкция", max_length=6000)

    class Meta:
        ordering = ["title"]
        verbose_name = "Процедура"
        verbose_name_plural = "Процедури"
        constraints = [
            models.UniqueConstraint(
                fields=["category", "title"], name="unique_procedure_title_in_category",
                violation_error_message="В тази категория вече има процедура с това заглавие.",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("procedures:detail", args=[self.pk])
