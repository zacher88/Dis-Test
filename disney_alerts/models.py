"""Domain models for Disney availability monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WatchType(StrEnum):
    """Kinds of Disney inventory the app can monitor."""

    DINING = "dining"
    LIGHTNING_LANE = "lightning_lane"
    DVC = "dvc"


@dataclass(frozen=True)
class WatchRequest:
    """A user's request to be alerted when inventory is available."""

    id: int | None
    watch_type: WatchType
    destination: str
    item_name: str
    party_size: int
    start_date: str
    end_date: str
    preferred_time: str
    contact: str
    active: bool = True


@dataclass(frozen=True)
class AvailabilityOpportunity:
    """A bookable opening returned by an availability provider."""

    watch_id: int
    watch_type: WatchType
    destination: str
    item_name: str
    available_date: str
    available_time: str
    booking_url: str
    notes: str
