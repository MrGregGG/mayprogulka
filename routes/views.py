import json
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET
from .models import Route


def home(request):
    return render(request, "routes/home.html")


@require_GET
def route_list(request):
    queryset = Route.objects.filter(is_published=True)
    year = request.GET.get("year")
    route_type = request.GET.get("type")
    start_place = request.GET.get("start")
    min_distance = request.GET.get("min_distance")
    max_distance = request.GET.get("max_distance")

    if year and year != "all":
        queryset = queryset.filter(event_year=year)
    if route_type and route_type != "all":
        queryset = queryset.filter(route_type=route_type)
    if start_place and start_place != "all":
        queryset = queryset.filter(start_place=start_place)
    try:
        if min_distance not in (None, ""):
            queryset = queryset.filter(official_distance_km__gte=float(min_distance))
        if max_distance not in (None, ""):
            queryset = queryset.filter(official_distance_km__lte=float(max_distance))
    except ValueError:
        return JsonResponse({"error": "Некорректный диапазон дистанции."}, status=400)

    routes = []
    for route in queryset:
        routes.append({
            "id": route.pk,
            "name": route.name,
            "year": route.event_year,
            "distance_km": float(route.official_distance_km),
            "type": route.route_type,
            "type_label": route.get_route_type_display(),
            "start_place": route.start_place or "Не указано",
            "points_count": route.points_count,
            "download_url": f"/routes/{route.pk}/download/",
            "geojson_url": f"/api/routes/{route.pk}/geojson/",
        })
    years = list(Route.objects.filter(is_published=True).values_list("event_year", flat=True).distinct().order_by("-event_year"))
    starts = list(Route.objects.filter(is_published=True).values_list("start_place", flat=True).distinct().order_by("start_place"))
    return JsonResponse({"routes": routes, "years": years, "starts": starts, "count": len(routes)})


@require_GET
def route_geojson(request, pk):
    route = get_object_or_404(Route, pk=pk, is_published=True)
    if not route.geojson:
        raise Http404("Геометрия маршрута пока не обработана.")
    return JsonResponse({
        "type": "Feature",
        "geometry": route.geojson,
        "properties": {
            "id": route.pk,
            "name": route.name,
            "year": route.event_year,
            "distance_km": float(route.official_distance_km),
            "start_place": route.start_place,
            "checkpoints": route.checkpoints,
        },
    })


@require_GET
def route_download(request, pk):
    route = get_object_or_404(Route, pk=pk, is_published=True)
    if not route.gpx_file:
        raise Http404("GPX-файл не найден.")
    filename = f"mayprogulka_{route.event_year}_{route.pk}.gpx"
    return FileResponse(route.gpx_file.open("rb"), as_attachment=True, filename=filename, content_type="application/gpx+xml")
