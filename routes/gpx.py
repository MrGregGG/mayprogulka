import math
import xml.etree.ElementTree as ET


class GPXError(ValueError):
    pass


def _local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _distance_m(a, b):
    lat1, lon1 = a[1], a[0]
    lat2, lon2 = b[1], b[0]
    radius = 6371008.8
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    h = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(min(1.0, h)))


def parse_gpx(file_obj):
    """Parse GPX into GeoJSON geometry, checkpoints and basic statistics."""
    try:
        raw = file_obj.read()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        root = ET.fromstring(raw)
    except (ET.ParseError, OSError, UnicodeError) as exc:
        raise GPXError("Не удалось прочитать GPX. Проверьте, что это корректный XML-файл.") from exc

    if _local_name(root.tag) != "gpx":
        raise GPXError("Файл не похож на GPX: корневой элемент должен быть gpx.")

    segments = []
    for trk in (el for el in root.iter() if _local_name(el.tag) == "trk"):
        trk_segments = [el for el in trk.iter() if _local_name(el.tag) == "trkseg"]
        for segment in trk_segments:
            points = []
            for point in segment:
                if _local_name(point.tag) != "trkpt":
                    continue
                coord = _read_coord(point)
                if coord:
                    points.append(coord)
            if len(points) >= 2:
                segments.append(points)

    if not segments:
        route_points = []
        for point in (el for el in root.iter() if _local_name(el.tag) == "rtept"):
            coord = _read_coord(point)
            if coord:
                route_points.append(coord)
        if len(route_points) >= 2:
            segments = [route_points]

    if not segments:
        raise GPXError("В GPX не найден маршрут минимум из двух GPS-точек.")

    all_points = [point for segment in segments for point in segment]
    distance_m = sum(_distance_m(a, b) for segment in segments for a, b in zip(segment, segment[1:]))

    checkpoints = []
    for waypoint in (el for el in root.iter() if _local_name(el.tag) == "wpt"):
        coord = _read_coord(waypoint)
        if not coord:
            continue
        name = ""
        for child in waypoint:
            if _local_name(child.tag) == "name" and child.text:
                name = child.text.strip()
                break
        checkpoints.append({"name": name or "Контрольная точка", "coordinates": coord})

    coordinates = [[[lon, lat] for lon, lat in segment] for segment in segments]
    if len(coordinates) == 1:
        geometry = {"type": "LineString", "coordinates": coordinates[0]}
    else:
        geometry = {"type": "MultiLineString", "coordinates": coordinates}

    first = all_points[0]
    last = all_points[-1]
    return {
        "geometry": geometry,
        "checkpoints": checkpoints,
        "points_count": len(all_points),
        "computed_distance_km": round(distance_m / 1000, 2),
        "start": first,
        "end": last,
    }


def _read_coord(element):
    try:
        lat = float(element.attrib["lat"])
        lon = float(element.attrib["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return [lon, lat]
