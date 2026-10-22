from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="Име")),
                ("description", models.TextField(blank=True, max_length=1000, verbose_name="Описание")),
            ],
            options={"verbose_name": "Категория", "verbose_name_plural": "Категории", "ordering": ["name"]},
        ),
    ]
