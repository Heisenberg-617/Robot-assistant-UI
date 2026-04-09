import json
import tempfile
import unittest
from pathlib import Path

from src.services.navigation import NavigationService


class NavigationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.locations_file = Path(self.temp_dir.name) / "locations.json"
        self.history_file = Path(self.temp_dir.name) / "history.json"

        self.locations_file.write_text(
            json.dumps(
                [
                    {
                        "location_name": "Reception",
                        "aliases": "front desk, accueil, help desk",
                        "description": "Visitor welcome area.",
                        "coordinates": {"latitude": 1.1, "longitude": 2.2},
                    },
                    {
                        "location_name": "Student Lounge",
                        "category": "Student Life",
                        "aliases": ["lounge", "hangout spot"],
                        "description": "Student social space.",
                        "coordinates": {"latitude": 3.3, "longitude": 4.4},
                    },
                ]
            ),
            encoding="utf-8",
        )

        self.navigation = NavigationService(
            locations_file=str(self.locations_file),
            history_file=str(self.history_file),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_alias_string_is_split_for_resolution(self) -> None:
        location = self.navigation.resolve_location("front desk")
        self.assertIsNotNone(location)
        self.assertEqual(location.location_name, "Reception")

    def test_resolve_location_supports_close_alias_match(self) -> None:
        location = self.navigation.resolve_location("hangout")
        self.assertIsNotNone(location)
        self.assertEqual(location.location_name, "Student Lounge")

    def test_search_locations_filters_by_category(self) -> None:
        results = self.navigation.search_locations(category="Student Life")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].location_name, "Student Lounge")

    def test_start_navigation_persists_history(self) -> None:
        payload = self.navigation.start_navigation("lounge", requested_by="test")
        self.assertIsNotNone(payload)
        self.assertEqual(payload["location_name"], "Student Lounge")
        self.assertIn("dispatch", payload)
        self.assertEqual(payload["dispatch"]["status"], "placeholder")

        history = self.navigation.get_history(limit=1)
        self.assertEqual(history[0]["location"], "Student Lounge")
        self.assertEqual(history[0]["requested_by"], "test")
        self.assertEqual(history[0]["dispatch"]["status"], "placeholder")


if __name__ == "__main__":
    unittest.main()
