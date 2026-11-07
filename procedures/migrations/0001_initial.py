import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("categories", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Procedure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120, verbose_name="Заглавие")),
                ("steps", models.TextField(max_length=6000, verbose_name="Инструкция")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="procedures", to="categories.category", verbose_name="Категория")),
            ],
            options={
                "verbose_name": "Процедура",
                "verbose_name_plural": "Процедури",
                "ordering": ["title"],
                "constraints": [models.UniqueConstraint(fields=("category", "title"), name="unique_procedure_title_in_category", violation_error_message="В тази категория вече има процедура с това заглавие.")],
            },
        ),
    ]
