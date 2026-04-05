"""Condition report comparison for check-in vs check-out photos."""

import io
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from PIL import Image


class Severity(Enum):
    """Severity level for detected damages."""

    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


# Cost ranges per severity level (EUR)
_COST_RANGES: dict[Severity, tuple[float, float]] = {
    Severity.MINOR: (50.0, 200.0),
    Severity.MODERATE: (200.0, 800.0),
    Severity.MAJOR: (800.0, 3000.0),
}


@dataclass
class DamageItem:
    """A single detected damage."""

    description: str
    severity: Severity
    location_in_image: str = ""


@dataclass
class RoomComparison:
    """Comparison result for a single room."""

    room_label: str
    damages: list[DamageItem] = field(default_factory=list)
    status: str = "no_change"  # no_change / minor_wear / damage_detected
    narrative: str = ""
    estimated_cost_min: float = 0.0
    estimated_cost_max: float = 0.0


@dataclass
class ConditionReportResult:
    """Full condition report comparison result."""

    rooms: list[RoomComparison] = field(default_factory=list)
    overall_summary: str = ""
    total_estimated_cost_min: float = 0.0
    total_estimated_cost_max: float = 0.0


class ConditionReportComparer:
    """Compares check-in vs check-out photos to detect damages."""

    MINOR_THRESHOLD = 0.02
    MODERATE_THRESHOLD = 0.08

    def _load_image(self, photo_bytes: bytes) -> np.ndarray | None:
        """Load image bytes into a normalized numpy array."""
        try:
            img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
            return np.array(img, dtype=np.float32) / 255.0
        except Exception:
            return None

    def _compute_difference_score(
        self, img_a: np.ndarray, img_b: np.ndarray
    ) -> float:
        """Compute mean absolute difference between two images."""
        # Resize to common dimensions if needed
        if img_a.shape != img_b.shape:
            min_h = min(img_a.shape[0], img_b.shape[0])
            min_w = min(img_a.shape[1], img_b.shape[1])
            img_a = img_a[:min_h, :min_w]
            img_b = img_b[:min_h, :min_w]
        return float(np.mean(np.abs(img_a - img_b)))

    def _classify_damage(self, diff_score: float) -> list[DamageItem]:
        """Classify damage based on pixel difference score."""
        if diff_score < self.MINOR_THRESHOLD:
            return []
        if diff_score < self.MODERATE_THRESHOLD:
            return [
                DamageItem(
                    description="Minor surface changes detected",
                    severity=Severity.MINOR,
                    location_in_image="Distributed across image",
                )
            ]
        return [
            DamageItem(
                description="Significant changes detected between photos",
                severity=Severity.MODERATE
                if diff_score < 0.15
                else Severity.MAJOR,
                location_in_image="Multiple areas affected",
            )
        ]

    def _compare_room_photos(
        self, check_in: list[bytes], check_out: list[bytes]
    ) -> tuple[list[DamageItem], float]:
        """Compare sets of photos for a single room."""
        all_damages: list[DamageItem] = []
        max_diff = 0.0

        pairs = min(len(check_in), len(check_out))
        for i in range(pairs):
            img_a = self._load_image(check_in[i])
            img_b = self._load_image(check_out[i])
            if img_a is None or img_b is None:
                continue
            diff = self._compute_difference_score(img_a, img_b)
            max_diff = max(max_diff, diff)
            damages = self._classify_damage(diff)
            all_damages.extend(damages)

        return all_damages, max_diff

    def compare_rooms(
        self,
        check_in_photos: dict[str, list[bytes]],
        check_out_photos: dict[str, list[bytes]],
    ) -> ConditionReportResult:
        """Compare check-in and check-out photos by room."""
        rooms: list[RoomComparison] = []
        total_min = 0.0
        total_max = 0.0
        all_labels = set(check_in_photos.keys()) | set(check_out_photos.keys())

        for label in sorted(all_labels):
            ci_photos = check_in_photos.get(label, [])
            co_photos = check_out_photos.get(label, [])

            if not ci_photos or not co_photos:
                status = "no_change"
                narrative = f"Warning: {label} missing "
                narrative += (
                    "check-out photos" if not co_photos else "check-in photos"
                )
                rooms.append(
                    RoomComparison(
                        room_label=label, status=status, narrative=narrative
                    )
                )
                continue

            damages, max_diff = self._compare_room_photos(ci_photos, co_photos)

            if not damages:
                status = "no_change"
                narrative = f"{label}: No significant changes detected"
            elif all(d.severity == Severity.MINOR for d in damages):
                status = "minor_wear"
                narrative = f"{label}: Minor wear detected"
            else:
                status = "damage_detected"
                narrative = f"{label}: Damage detected, review recommended"

            cost_min = sum(_COST_RANGES[d.severity][0] for d in damages)
            cost_max = sum(_COST_RANGES[d.severity][1] for d in damages)
            total_min += cost_min
            total_max += cost_max

            rooms.append(
                RoomComparison(
                    room_label=label,
                    damages=damages,
                    status=status,
                    narrative=narrative,
                    estimated_cost_min=cost_min,
                    estimated_cost_max=cost_max,
                )
            )

        damage_count = sum(len(r.damages) for r in rooms)
        if damage_count == 0:
            summary = "No damages detected across all rooms"
        else:
            summary = f"Detected {damage_count} damage(s) across {len(rooms)} room(s)"

        return ConditionReportResult(
            rooms=rooms,
            overall_summary=summary,
            total_estimated_cost_min=total_min,
            total_estimated_cost_max=total_max,
        )
