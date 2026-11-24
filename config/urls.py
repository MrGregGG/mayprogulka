from django.contrib import admin
from django.urls import path
from routes import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("api/routes/", views.route_list, name="route-list"),
    path("api/routes/<int:pk>/geojson/", views.route_geojson, name="route-geojson"),
    path("routes/<int:pk>/download/", views.route_download, name="route-download"),
]
