import json
from rapidfuzz import process, fuzz
from datetime import datetime

class NavigationService:
    """Service to handle navigation-related tasks, such as retrieving coordinates for a location and interfacing with ROS."""

    def __init__(self, locations_file: str = "data/locations.json", history_file: str = "data/Navigation history/history.json"):
        self.locations_file = locations_file
        self.history_file = history_file

    def get_coordinates(self, user_input: str):
        with open(self.locations_file, "r") as f:
            locations = json.load(f)

        # Build a mapping of location names and aliases to their coordinates
        name_to_coords = {}
        for loc in locations:
            coords = (loc["coordinates"]["latitude"], loc["coordinates"]["longitude"])
            name_to_coords[loc["location_name"].lower()] = coords
            if "aliases" in loc:
                for alias in loc["aliases"]:
                    name_to_coords[alias.lower()] = coords

        # Use fuzzy matching to find the closest location
        match, score, _ = process.extractOne(user_input.lower(), name_to_coords.keys(), scorer=fuzz.WRatio)
        if score < 60:  # threshold can be tuned
            return None, None  # no good match
        
        # Add coordinates to the navigation history
        lat, long = name_to_coords[match]
        with open(self.history_file, "a") as f:
            history = json.load(f)
            # Append new entry
            history.append({
                "location": user_input,
                "date": datetime.utcnow().isoformat(),
                "coordinates": {"latitude": lat, "longitude": long}
            })
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=4)

        return name_to_coords[match]            