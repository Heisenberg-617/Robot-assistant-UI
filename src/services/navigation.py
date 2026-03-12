import json
from rapidfuzz import process, fuzz

class NavigationService:
    """Service to handle navigation-related tasks, such as retrieving coordinates for a location and interfacing with ROS."""

    def __init__(self, locations_file: str = "data/locations.json"):
        self.locations_file = locations_file
        
    def get_coordinates(self, user_input: str):
        with open(self.locations_file, "r") as f:
            locations = json.load(f)

        # Build a mapping of location names to their coordinates
        name_to_coords = {loc["location_name"].lower(): (loc["coordinates"]["latitude"], loc["coordinates"]["longitude"]) for loc in locations}

        # Use fuzzy matching to find the closest location
        match, score, _ = process.extractOne(user_input.lower(), name_to_coords.keys(), scorer=fuzz.WRatio)
        if score < 60:  # threshold can be tuned
            return None, None  # no good match
        return name_to_coords[match]