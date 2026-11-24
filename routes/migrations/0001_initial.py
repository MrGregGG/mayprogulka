from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Route",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180, verbose_name="Название маршрута")),
                ("event_year", models.PositiveSmallIntegerField(db_index=True, verbose_name="Год мероприятия")),
                ("official_distance_km", models.DecimalField(decimal_places=1, max_digits=6, verbose_name="Официальная дистанция, км")),
                ("route_type", models.CharField(choices=[("unknown", "Не указан"), ("walking", "Пеший"), ("cycling", "Велосипедный")], db_index=True, default="unknown", max_length=12, verbose_name="Тип маршрута")),
                ("start_place", models.CharField(blank=True, db_index=True, default="Не указано", max_length=180, verbose_name="Место старта")),
                ("start_lat", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True, verbose_name="Широта начала трека")),
                ("start_lon", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True, verbose_name="Долгота начала трека")),
                ("gpx_file", models.FileField(blank=True, upload_to="routes/%Y/", verbose_name="GPX-файл")),
                ("geojson", models.JSONField(blank=True, default=dict, verbose_name="Геометрия маршрута")),
                ("checkpoints", models.JSONField(blank=True, default=list, verbose_name="Контрольные точки")),
                ("points_count", models.PositiveIntegerField(default=0, verbose_name="Количество GPS-точек")),
                ("computed_distance_km", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name="Длина по GPX, км")),
                ("is_published", models.BooleanField(db_index=True, default=True, verbose_name="Опубликован")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")),
            ],
            options={
                "verbose_name": "Маршрут",
                "verbose_name_plural": "Маршруты",
                "ordering": ["-event_year", "official_distance_km", "name"],
            },
        ),
    ]
