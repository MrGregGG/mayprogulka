from django.db import models


class Route(models.Model):
    TYPE_UNKNOWN = "unknown"
    TYPE_WALKING = "walking"
    TYPE_CYCLING = "cycling"
    TYPE_CHOICES = [
        (TYPE_UNKNOWN, "Не указан"),
        (TYPE_WALKING, "Пеший"),
        (TYPE_CYCLING, "Велосипедный"),
    ]

    name = models.CharField("Название маршрута", max_length=180)
    event_year = models.PositiveSmallIntegerField("Год мероприятия", db_index=True)
    official_distance_km = models.DecimalField("Официальная дистанция, км", max_digits=6, decimal_places=1)
    route_type = models.CharField("Тип маршрута", max_length=12, choices=TYPE_CHOICES, default=TYPE_UNKNOWN, db_index=True)
    start_place = models.CharField("Место старта", max_length=180, blank=True, default="Не указано", db_index=True)
    start_lat = models.DecimalField("Широта начала трека", max_digits=10, decimal_places=7, blank=True, null=True)
    start_lon = models.DecimalField("Долгота начала трека", max_digits=10, decimal_places=7, blank=True, null=True)
    gpx_file = models.FileField("GPX-файл", upload_to="routes/%Y/", blank=True)
    geojson = models.JSONField("Геометрия маршрута", default=dict, blank=True)
    checkpoints = models.JSONField("Контрольные точки", default=list, blank=True)
    points_count = models.PositiveIntegerField("Количество GPS-точек", default=0)
    computed_distance_km = models.DecimalField("Длина по GPX, км", max_digits=8, decimal_places=2, blank=True, null=True)
    is_published = models.BooleanField("Опубликован", default=True, db_index=True)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        ordering = ["-event_year", "official_distance_km", "name"]
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"

    def __str__(self):
        return f"{self.event_year} · {self.name} · {self.official_distance_km} км"
