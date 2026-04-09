import json
import re
from difflib import SequenceMatcher
from dataclasses import replace
from pathlib import Path
from typing import Iterable, List, Optional
from unicodedata import normalize

from src.models import Destination


DEFAULT_CATEGORY_BY_NAME = {
    "cafeteria": "alimentation",
    "cafétéria": "alimentation",
    "student lounge": "détente",
    "foyer étudiant": "détente",
    "administration": "administratif",
    "reception": "administratif",
    "réception": "administratif",
    "accueil": "administratif",
    "health center": "santé",
    "centre de santé": "santé",
    "laboratoire de physique expérimentale": "laboratoire",
    "laboratoire de projet d'ingénierie": "laboratoire",
    "laboratoire de mécatronique": "laboratoire",
    "radio étudiante": "média",
    "bureau e-tech": "clubs",
    "bureau e-olive": "clubs",
    "bureau e-mix": "clubs",
    "service d'impression": "services",
}


class LocationCatalogService:
    def __init__(self, locations_file: str = "data/locations.json"):
        self.locations_file = Path(locations_file)
        self._locations = self._load_locations()

    def _load_locations(self) -> List[Destination]:
        with self.locations_file.open("r", encoding="utf-8") as handle:
            raw_locations = json.load(handle)

        locations: List[Destination] = []
        for raw_location in raw_locations:
            coords = raw_location.get("coordinates", {})
            location_name = str(raw_location.get("location_name", "")).strip()
            aliases = self._normalize_aliases(raw_location.get("aliases"))
            category = self._normalize_category(
                raw_location.get("category"),
                location_name,
            )

            locations.append(
                Destination(
                    location_name=location_name,
                    category=category,
                    description=str(raw_location.get("description", "")).strip(),
                    latitude=float(coords.get("latitude", 0.0)),
                    longitude=float(coords.get("longitude", 0.0)),
                    building=str(raw_location.get("building", "")).strip(),
                    floor=str(raw_location.get("floor", "")).strip(),
                    accessible=bool(raw_location.get("accessible", False)),
                    aliases=aliases,
                )
            )

        return sorted(locations, key=lambda location: (location.category, location.location_name))

    def _normalize_aliases(self, raw_aliases: object) -> List[str]:
        if raw_aliases is None:
            return []

        values: Iterable[object]
        if isinstance(raw_aliases, list):
            values = raw_aliases
        elif isinstance(raw_aliases, str):
            values = raw_aliases.split(",")
        else:
            values = [raw_aliases]

        aliases: List[str] = []
        seen: set[str] = set()
        for raw_alias in values:
            alias = " ".join(str(raw_alias).strip().split())
            if not alias:
                continue

            alias_key = alias.lower()
            if alias_key in seen:
                continue

            seen.add(alias_key)
            aliases.append(alias)

        return aliases

    def _normalize_category(self, raw_category: object, location_name: str) -> str:
        category = str(raw_category or "").strip()
        if category:
            return category
        return DEFAULT_CATEGORY_BY_NAME.get(location_name.lower(), "services")

    def list_locations(self) -> List[Destination]:
        return list(self._locations)

    def get_categories(self) -> List[str]:
        return sorted({location.category for location in self._locations})

    def get_location(self, location_name: str) -> Optional[Destination]:
        lookup = self._normalize_text(location_name)
        for location in self._locations:
            if self._normalize_text(location.location_name) == lookup:
                return location
        return None

    def search_locations(
        self,
        query: str = "",
        category: str = "All",
        limit: Optional[int] = None,
    ) -> List[Destination]:
        normalized_query = self._normalize_text(query)
        normalized_category = self._normalize_text(category)

        filtered = [
            location
            for location in self._locations
            if (
                normalized_category in {"", "all", "toutes"}
                or normalized_category.startswith("toutes les cat")
                or normalized_category.startswith("tous les empl")
            )
            or self._normalize_text(location.category) == normalized_category
        ]

        if not normalized_query:
            return filtered[:limit] if limit else filtered

        query_tokens = [token for token in normalized_query.split() if token]
        matching_locations = [
            location
            for location in filtered
            if all(token in self._normalize_text(location.location_name) for token in query_tokens)
        ]
        return matching_locations[:limit] if limit else matching_locations

    def resolve_location(self, user_input: str, threshold: int = 60) -> Optional[Destination]:
        normalized_input = self._normalize_text(user_input)
        if not normalized_input:
            return None

        choices: dict[str, tuple[Destination, bool]] = {}
        for location in self._locations:
            choices[location.location_name] = (location, False)
            for alias in location.aliases:
                choices[alias] = (location, True)

        best_match_name = None
        best_score = 0
        for candidate, (location, is_alias) in choices.items():
            candidate_lower = self._normalize_text(candidate)
            if normalized_input == candidate_lower:
                best_match_name = candidate
                best_score = 100
                break

            score = self._location_match_score(normalized_input, candidate_lower, is_alias=is_alias)

            if score > best_score:
                best_score = score
                best_match_name = candidate

        if not best_match_name or best_score < threshold:
            return None

        matched_name = str(best_match_name)
        return replace(choices[matched_name][0], matched_name=matched_name)

    def _normalize_text(self, value: str) -> str:
        normalized = normalize("NFKD", value or "")
        return "".join(char for char in normalized if ord(char) < 128).lower().strip()

    def _location_match_score(self, query: str, candidate: str, *, is_alias: bool) -> int:
        if not query or not candidate:
            return 0

        if query == candidate:
            return 100

        query_tokens = self._tokenize(query)
        candidate_tokens = self._tokenize(candidate)
        candidate_token_set = set(candidate_tokens)

        overlap = sum(token in candidate_token_set for token in query_tokens)
        overlap_score = int((overlap / max(len(query_tokens), 1)) * 100)
        similarity_score = int(SequenceMatcher(None, query, candidate).ratio() * 100)

        score = max(similarity_score, overlap_score)
        if query in candidate:
            score = max(score, 92 if is_alias else 88)

        if candidate in query:
            score = max(score, 86 if is_alias else 82)

        has_strong_overlap = overlap > 0 or query in candidate or candidate in query
        if not has_strong_overlap and similarity_score < 78:
            score = max(0, similarity_score - 35)

        if is_alias:
            score += 4

        return min(score, 100)

    def _tokenize(self, value: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", value)

