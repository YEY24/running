import unittest
from sync_intervals import encode_route, export, normalize


class SyncTests(unittest.TestCase):
    def test_polyline_reference_vector(self):
        self.assertEqual(encode_route([{"type": "latlng", "data": [38.5, 40.7, 43.252], "data2": [-120.2, -120.95, -126.453]}]), "_p~iF~ps|U_ulLnnqC_mqNvxq`@")

    def test_route_handles_missing_and_duplicates(self):
        self.assertIsNone(encode_route([{"type": "latlng", "data": [None, 1, 1], "data2": [2, 2, 2]}]))
        with self.assertRaises(ValueError):
            encode_route([{"type": "latlng", "data": [1], "data2": []}])

    def test_metrics_units_and_private_fields(self):
        row = normalize({"id": "i123", "type": "Run", "start_date_local": "2026-10-30T08:00:00", "distance": 10000, "moving_time": 3000, "name": "Home address", "average_heartrate": 160}, None)
        self.assertEqual(row["moving_time"], "0:50:00")
        self.assertAlmostEqual(row["average_speed"], 10 / 3)
        self.assertEqual(row["name"], "Run")
        self.assertIsNone(row["average_heartrate"])

    def test_full_snapshot_filter_stubs_and_distinct_ids(self):
        base = {"type": "Run", "start_date_local": "2026-10-30T08:00:00", "distance": 1000, "moving_time": 300, "stream_types": ["latlng"]}
        seen = []
        def fetch(path):
            seen.append(path)
            if "/athlete/" in path:
                return [{**base, "id": "i1"}, {**base, "id": "1"}, {"id": "stub"}, {**base, "id": "bike", "type": "Ride"}]
            return [{"type": "latlng", "data": [49, 49.1], "data2": [8, 8.1]}]
        rows, skipped = export(fetch, "0")
        self.assertEqual(len(rows), 2)
        self.assertEqual(skipped, 1)
        self.assertEqual({r["run_id"] for r in rows}, {"i1", "1"})
        self.assertEqual(len(seen), 3)
        seen.clear()
        rows, _ = export(fetch, "0", routes=False)
        self.assertEqual(len(seen), 1)
        self.assertTrue(all(r["summary_polyline"] is None for r in rows))

    def test_api_failure_aborts_export(self):
        def fail(_):
            raise RuntimeError("HTTP 401")
        with self.assertRaises(RuntimeError):
            export(fail, "0")


if __name__ == "__main__":
    unittest.main()
