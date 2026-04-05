"""Unit tests for condition report comparison."""

import io

import numpy as np
from PIL import Image

from src.models.condition_report import (
    ConditionReportComparer,
    ConditionReportResult,
    RoomComparison,
    Severity,
)


def _make_solid_image(
    color: tuple[int, int, int] = (128, 128, 128),
    width: int = 100,
    height: int = 100,
) -> bytes:
    """Create a solid-color image as bytes."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _make_noisy_image(width: int = 100, height: int = 100) -> bytes:
    """Create a random-noise image as bytes."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


class TestConditionReportComparer:
    """Tests for the condition report comparison logic."""

    def test_identical_photos_no_damage(self) -> None:
        """Identical check-in and check-out photos should detect no damage."""
        comparer = ConditionReportComparer()
        photo = _make_solid_image(color=(200, 200, 200))
        result = comparer.compare_rooms(
            check_in_photos={"kitchen": [photo]},
            check_out_photos={"kitchen": [photo]},
        )
        assert len(result.rooms) == 1
        assert result.rooms[0].status == "no_change"
        assert result.rooms[0].damages == []
        assert result.total_estimated_cost_min == 0.0

    def test_different_photos_detects_damage(self) -> None:
        """Very different photos should detect damage."""
        comparer = ConditionReportComparer()
        check_in = _make_solid_image(color=(255, 255, 255))
        check_out = _make_solid_image(color=(0, 0, 0))
        result = comparer.compare_rooms(
            check_in_photos={"bedroom": [check_in]},
            check_out_photos={"bedroom": [check_out]},
        )
        assert len(result.rooms) == 1
        room = result.rooms[0]
        assert room.status == "damage_detected"
        assert len(room.damages) > 0
        assert result.total_estimated_cost_min > 0

    def test_unmatched_room_warning(self) -> None:
        """A room present only in check-out should produce a warning."""
        comparer = ConditionReportComparer()
        photo = _make_solid_image()
        result = comparer.compare_rooms(
            check_in_photos={"kitchen": [photo]},
            check_out_photos={"kitchen": [photo], "bathroom": [photo]},
        )
        bathroom = next(r for r in result.rooms if r.room_label == "bathroom")
        assert "missing" in bathroom.narrative.lower() or "Warning" in bathroom.narrative

    def test_room_missing_checkout_photos(self) -> None:
        """A room with check-in but no check-out photos should produce a warning."""
        comparer = ConditionReportComparer()
        photo = _make_solid_image()
        result = comparer.compare_rooms(
            check_in_photos={"kitchen": [photo], "living_room": [photo]},
            check_out_photos={"kitchen": [photo]},
        )
        lr = next(r for r in result.rooms if r.room_label == "living_room")
        assert "missing" in lr.narrative.lower()

    def test_empty_input_returns_empty(self) -> None:
        """No rooms should return an empty result."""
        comparer = ConditionReportComparer()
        result = comparer.compare_rooms(
            check_in_photos={},
            check_out_photos={},
        )
        assert result.rooms == []
        assert result.total_estimated_cost_min == 0.0

    def test_cost_estimation_ranges(self) -> None:
        """Detected damages should have cost estimates within severity ranges."""
        comparer = ConditionReportComparer()
        check_in = _make_solid_image(color=(255, 255, 255))
        check_out = _make_solid_image(color=(0, 0, 0))
        result = comparer.compare_rooms(
            check_in_photos={"room": [check_in]},
            check_out_photos={"room": [check_out]},
        )
        room = result.rooms[0]
        assert room.estimated_cost_min >= 50.0
        assert room.estimated_cost_max >= room.estimated_cost_min

    def test_multiple_rooms_aggregation(self) -> None:
        """Total costs should aggregate across all rooms."""
        comparer = ConditionReportComparer()
        clean = _make_solid_image(color=(200, 200, 200))
        damaged_in = _make_solid_image(color=(255, 255, 255))
        damaged_out = _make_solid_image(color=(0, 0, 0))
        result = comparer.compare_rooms(
            check_in_photos={"kitchen": [clean], "bedroom": [damaged_in]},
            check_out_photos={"kitchen": [clean], "bedroom": [damaged_out]},
        )
        assert len(result.rooms) == 2
        bedroom = next(r for r in result.rooms if r.room_label == "bedroom")
        kitchen = next(r for r in result.rooms if r.room_label == "kitchen")
        assert bedroom.estimated_cost_min > 0
        assert kitchen.estimated_cost_min == 0
        assert result.total_estimated_cost_min == bedroom.estimated_cost_min
