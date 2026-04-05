"""Listing duplication detection using text, image, and location similarity."""

import math
from dataclasses import dataclass, field


@dataclass
class DuplicateReport:
    """Result of duplicate listing detection."""

    duplication_score: float
    text_similarity: float
    image_similarity: float
    location_proximity: float
    matched_listing_ids: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class CandidateListing:
    """A candidate listing to compare against for duplication."""

    listing_id: str
    title: str = ""
    description: str = ""
    image_phashes: list[str] = field(default_factory=list)
    latitude: float = 0.0
    longitude: float = 0.0


class DuplicationDetector:
    """Detects duplicate listings using text, image, and location similarity."""

    EARTH_RADIUS_KM = 6371.0
    CLOSE_DISTANCE_M = 50.0
    FAR_DISTANCE_M = 5000.0

    def compute_text_similarity(self, text_a: str, text_b: str) -> float:
        """Jaccard similarity on word sets as a baseline."""
        if not text_a or not text_b:
            return 0.0
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)

    def compute_image_similarity(self, phash_a: str, phash_b: str) -> float:
        """Hamming distance on perceptual hashes (hex strings)."""
        if not phash_a or not phash_b:
            return 0.0
        try:
            int_a = int(phash_a, 16)
            int_b = int(phash_b, 16)
        except ValueError:
            return 0.0
        xor = int_a ^ int_b
        hamming = bin(xor).count("1")
        hash_bits = max(len(phash_a), len(phash_b)) * 4
        if hash_bits == 0:
            return 0.0
        return max(0.0, 1.0 - hamming / hash_bits)

    def compute_location_proximity(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Haversine distance, score=1 if <50m, decays to 0 at 5km."""
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_m = self.EARTH_RADIUS_KM * c * 1000

        if distance_m <= self.CLOSE_DISTANCE_M:
            return 1.0
        if distance_m >= self.FAR_DISTANCE_M:
            return 0.0
        # Linear decay between 50m and 5000m
        return 1.0 - (distance_m - self.CLOSE_DISTANCE_M) / (
            self.FAR_DISTANCE_M - self.CLOSE_DISTANCE_M
        )

    def detect(
        self,
        title: str,
        description: str,
        image_phashes: list[str],
        latitude: float,
        longitude: float,
        candidates: list[CandidateListing],
    ) -> DuplicateReport:
        """Detect if a listing is a duplicate of any candidate."""
        if not candidates:
            return DuplicateReport(
                duplication_score=0.0,
                text_similarity=0.0,
                image_similarity=0.0,
                location_proximity=0.0,
            )

        source_text = f"{title} {description}"
        best_text_sim = 0.0
        best_image_sim = 0.0
        best_location_prox = 0.0
        matched_ids: list[str] = []

        for candidate in candidates:
            cand_text = f"{candidate.title} {candidate.description}"
            text_sim = self.compute_text_similarity(source_text, cand_text)

            img_sim = 0.0
            for ph_a in image_phashes:
                for ph_b in candidate.image_phashes:
                    img_sim = max(
                        img_sim, self.compute_image_similarity(ph_a, ph_b)
                    )

            loc_prox = self.compute_location_proximity(
                latitude, longitude, candidate.latitude, candidate.longitude
            )

            content_sim = max(text_sim, img_sim)
            dup_score = content_sim * (0.5 + 0.5 * loc_prox)

            if dup_score > 0.5:
                matched_ids.append(candidate.listing_id)

            best_text_sim = max(best_text_sim, text_sim)
            best_image_sim = max(best_image_sim, img_sim)
            best_location_prox = max(best_location_prox, loc_prox)

        overall = max(best_text_sim, best_image_sim) * (
            0.5 + 0.5 * best_location_prox
        )

        return DuplicateReport(
            duplication_score=overall,
            text_similarity=best_text_sim,
            image_similarity=best_image_sim,
            location_proximity=best_location_prox,
            matched_listing_ids=matched_ids,
            summary=f"Found {len(matched_ids)} potential duplicates",
        )
