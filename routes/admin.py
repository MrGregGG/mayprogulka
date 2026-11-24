from django.contrib import admin
from django.utils.html import format_html
from .forms import RouteAdminForm
from .gpx import GPXError, parse_gpx
from .models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    form = RouteAdminForm
    list_display = ("name", "event_year", "official_distance_km", "route_type", "start_place", "points_count", "is_published")
    list_filter = ("event_year", "route_type", "is_published")
    search_fields = ("name", "start_place")
    list_editable = ("route_type", "is_published")
    ordering = ("-event_year", "official_distance_km")
    readonly_fields = ("points_count", "computed_distance_km", "created_at", "preview_note")
    fieldsets = (
        ("Основная информация", {"fields": ("name", "event_year", "official_distance_km", "route_type", "start_place", "is_published")}),
        ("GPX-файл", {"fields": ("gpx_file", "preview_note", "points_count", "computed_distance_km")}),
        ("Служебная информация", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    @admin.display(description="Статус обработки")
    def preview_note(self, obj):
        if obj and obj.pk and obj.points_count:
            return format_html("GPX обработан: {} точек, длина по координатам {} км", obj.points_count, obj.computed_distance_km or "не рассчитана")
        return "После сохранения GPX будет обработан автоматически."

    def save_model(self, request, obj, form, change):
        new_file = "gpx_file" in form.changed_data or not obj.geojson
        super().save_model(request, obj, form, change)
        if new_file and obj.gpx_file:
            try:
                with obj.gpx_file.open("rb") as file_obj:
                    parsed = parse_gpx(file_obj)
                obj.geojson = parsed["geometry"]
                obj.checkpoints = parsed["checkpoints"]
                obj.points_count = parsed["points_count"]
                obj.computed_distance_km = parsed["computed_distance_km"]
                obj.start_lon = parsed["start"][0]
                obj.start_lat = parsed["start"][1]
                obj.save(update_fields=["geojson", "checkpoints", "points_count", "computed_distance_km", "start_lat", "start_lon"])
            except GPXError as exc:
                self.message_user(request, str(exc), level="ERROR")
