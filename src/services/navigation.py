import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.models import Destination
from src.services.location_catalog import LocationCatalogService


class NavigationService:
    """Service to handle destination lookup and navigation start requests."""

    def __init__(
        self,
        locations_file: str = "data/locations.json",
        history_file: str = "data/Navigation history/history.json",
    ):
        self.catalog = LocationCatalogService(locations_file=locations_file)
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.robot_navigation_api_url = os.getenv("ROBOT_NAVIGATION_API_URL", "").strip()

    def list_locations(self):
        return self.catalog.list_locations()

    def get_categories(self):
        return ["All", *self.catalog.get_categories()]

    def search_locations(self, query: str = "", category: str = "All", limit: Optional[int] = None):
        return self.catalog.search_locations(query=query, category=category, limit=limit)

    def resolve_location(self, user_input: str) -> Optional[Destination]:
        return self.catalog.resolve_location(user_input)

    def prepare_navigation(self, user_input: str) -> Optional[dict]:
        location = self.resolve_location(user_input)
        if not location:
            return None

        # Use getattr so it doesn't crash if the attribute is missing
        matched = getattr(location, 'matched_name', None) or location.location_name

        return {
            "location_name": location.location_name,
            "category": location.category,
            "description": location.description,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "building": location.building,
            "floor": location.floor,
            "accessible": location.accessible,
            "matched_name": matched,
        }

    def get_coordinates(self, user_input: str):
        location = self.prepare_navigation(user_input)
        if not location:
            return None, None
        return location["latitude"], location["longitude"]

    def start_navigation(self, user_input: str, requested_by: str = "ui") -> Optional[dict]:
        navigation_payload = self.prepare_navigation(user_input)
        if not navigation_payload:
            return None

        dispatch_result = self._dispatch_navigation_command(navigation_payload)
        navigation_payload["dispatch"] = dispatch_result

        history = self._read_history()
        history.append(
            {
                "location": navigation_payload["location_name"],
                "matched_name": navigation_payload["matched_name"],
                "category": navigation_payload["category"],
                "date": datetime.now(timezone.utc).isoformat(),
                "requested_by": requested_by,
                "coordinates": {
                    "latitude": navigation_payload["latitude"],
                    "longitude": navigation_payload["longitude"],
                },
                "dispatch": dispatch_result,
            }
        )
        self._write_history(history)

        return navigation_payload

    def get_history(self, limit: Optional[int] = None) -> list[dict]:
        history = list(reversed(self._read_history()))
        return history[:limit] if limit else history

    def _read_history(self) -> list[dict]:
        try:
            with self.history_file.open("r", encoding="utf-8") as handle:
                try:
                    return json.load(handle)
                except json.JSONDecodeError:
                    return []
        except FileNotFoundError:
            return []

    def _write_history(self, history: list[dict]) -> None:
        with self.history_file.open("w", encoding="utf-8") as handle:
            json.dump(history, handle, indent=4, ensure_ascii=False)

    def _dispatch_navigation_command(self, navigation_payload: dict) -> dict:
        command_payload = {
            "destination": navigation_payload["location_name"],
            "matched_name": navigation_payload["matched_name"],
            "coordinates": {
                "latitude": navigation_payload["latitude"],
                "longitude": navigation_payload["longitude"],
            },
            "building": navigation_payload["building"],
            "floor": navigation_payload["floor"],
        }

        # Placeholder until the robot ROS API endpoint is available in this app environment.
        # Example integration:
        # import urllib.request
        #
        # request = urllib.request.Request(
        #     url=f"{self.robot_navigation_api_url.rstrip('/')}/navigation/start",
        #     data=json.dumps(command_payload).encode("utf-8"),
        #     headers={"Content-Type": "application/json"},
        #     method="POST",
        # )
        # with urllib.request.urlopen(request, timeout=10) as response:
        #     return json.loads(response.read().decode("utf-8"))
        #
        # The ROS-side API would then translate this payload into the actual navigation goal.
        return {
            "status": "placeholder",
            "message": "Navigation command prepared. Connect ROBOT_NAVIGATION_API_URL to send it to ROS.",
            "api_url": self.robot_navigation_api_url or None,
            "command_payload": command_payload,
        }
