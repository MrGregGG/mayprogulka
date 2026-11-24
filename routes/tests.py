from io import BytesIO
from pathlib import Path
from django.test import SimpleTestCase
from .gpx import GPXError, parse_gpx


class GPXParserTests(SimpleTestCase):
    def test_parses_line_and_checkpoints(self):
        content = b'''<?xml version="1.0"?><gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
        <wpt lat="56.8" lon="60.6"><name>Start</name></wpt>
        <trk><trkseg><trkpt lat="56.8" lon="60.6"/><trkpt lat="56.81" lon="60.61"/></trkseg></trk></gpx>'''
        result = parse_gpx(BytesIO(content))
        self.assertEqual(result["geometry"]["type"], "LineString")
        self.assertEqual(result["points_count"], 2)
        self.assertEqual(result["checkpoints"][0]["name"], "Start")
        self.assertGreater(result["computed_distance_km"], 0)

    def test_rejects_non_gpx_xml(self):
        with self.assertRaises(GPXError):
            parse_gpx(BytesIO(b"<not-gpx />"))
