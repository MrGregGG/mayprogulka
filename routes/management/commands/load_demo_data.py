from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from routes.gpx import parse_gpx
from routes.models import Route


ROUTES = [
    ("mp2024_10.gpx", 2024, "10 км · Полупроменад", 10.0, "Напротив корпуса УрФУ, ул. Мира, 28"),
    ("mp2024_17i.gpx", 2024, "17 км · Исетский променад", 17.0, "Напротив корпуса УрФУ, ул. Мира, 28"),
    ("mp2024_17s.gpx", 2024, "17 км · Шарташская кругосветка", 17.0, "Напротив корпуса УрФУ, ул. Мира, 28"),
    ("mp2024_35.gpx", 2024, "35 км · В район Новокольцовский", 35.0, "Напротив корпуса УрФУ, ул. Мира, 28"),
    ("mp2024_50.gpx", 2024, "50 км · Классика", 50.0, "Напротив корпуса УрФУ, ул. Мира, 28"),
    ("mp2025_14.gpx", 2025, "14 км · Исетский променад", 14.0, "Стадион УрФУ, ул. С. Набойченко, 4"),
    ("mp2025_17.gpx", 2025, "17 км · Шарташская кругосветка", 17.0, "Стадион УрФУ, ул. С. Набойченко, 4"),
    ("mp2025_33.gpx", 2025, "33 км · В район Новокольцовский", 33.0, "Стадион УрФУ, ул. С. Набойченко, 4"),
    ("mp2025_50.gpx", 2025, "50 км · Классика", 50.0, "Стадион УрФУ, ул. С. Набойченко, 4"),
    ("mp2026_15.gpx", 2026, "15 км · Городской маршрут", 15.0, "Площадь между стадионом УрФУ и зданием СКИФС"),
    ("mp2026_18.gpx", 2026, "18 км · Шарташская кругосветка", 18.0, "Площадь между стадионом УрФУ и зданием СКИФС"),
    ("mp2026_33.gpx", 2026, "30+3 км · Юбилейный мотив", 33.0, "Площадь между стадионом УрФУ и зданием СКИФС"),
    ("mp2026_50.gpx", 2026, "50 км · Классика", 50.0, "Площадь между стадионом УрФУ и зданием СКИФС"),
]


class Command(BaseCommand):
    help = "Импортирует демонстрационные маршруты Майской прогулки за 2024–2026 годы."

    def handle(self, *args, **options):
        source_dir = Path(settings.BASE_DIR) / "data" / "gpx"
        created = 0
        updated = 0
        for filename, year, name, distance, start_place in ROUTES:
            path = source_dir / filename
            if not path.exists():
                self.stderr.write(self.style.ERROR(f"Не найден файл: {path}"))
                continue
            with path.open("rb") as source:
                parsed = parse_gpx(source)
            route, was_created = Route.objects.get_or_create(
                event_year=year,
                name=name,
                defaults={
                    "official_distance_km": distance,
                    "route_type": Route.TYPE_WALKING,
                    "start_place": start_place,
                    "geojson": parsed["geometry"],
                    "checkpoints": parsed["checkpoints"],
                    "points_count": parsed["points_count"],
                    "computed_distance_km": parsed["computed_distance_km"],
                    "start_lon": parsed["start"][0],
                    "start_lat": parsed["start"][1],
                    "is_published": True,
                    "gpx_file": ContentFile(path.read_bytes(), name=filename),
                },
            )
            if was_created:
                created += 1
            else:
                route.official_distance_km = distance
                route.route_type = Route.TYPE_WALKING
                route.start_place = start_place
                route.geojson = parsed["geometry"]
                route.checkpoints = parsed["checkpoints"]
                route.points_count = parsed["points_count"]
                route.computed_distance_km = parsed["computed_distance_km"]
                route.start_lon = parsed["start"][0]
                route.start_lat = parsed["start"][1]
                if not route.gpx_file:
                    route.gpx_file.save(filename, ContentFile(path.read_bytes(), name=filename), save=False)
                route.save()
                updated += 1
            self.stdout.write(f"{year}: {name}, {parsed['points_count']} точек, GPX {parsed['computed_distance_km']} км")
        self.stdout.write(self.style.SUCCESS(f"Готово. Добавлено: {created}, обновлено: {updated}."))
