"""Availability provider adapters.

The prototype ships with deterministic mock data so the web app can be used and
validated without scraping Disney websites. A production implementation should
prefer official APIs, partner feeds, or user-authorized integrations before any
scraping is considered.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Protocol

from .models import AvailabilityOpportunity, WatchRequest, WatchType


class AvailabilityProvider(Protocol):
    """Interface for services that can search Disney inventory."""

    def search(self, watch: WatchRequest) -> list[AvailabilityOpportunity]:
        """Return currently available opportunities for a watch request."""


class MockAvailabilityProvider:
    """Deterministic provider used for local development and tests."""

    def search(self, watch: WatchRequest) -> list[AvailabilityOpportunity]:
        if not watch.active:
            return []

        normalized_name = watch.item_name.lower()
        openings: list[AvailabilityOpportunity] = []

        if watch.watch_type == WatchType.DINING and "ohana" in normalized_name:
            openings.append(
                AvailabilityOpportunity(
                    watch_id=watch.id or 0,
                    watch_type=watch.watch_type,
                    destination=watch.destination,
                    item_name=watch.item_name,
                    available_date=watch.start_date,
                    available_time=watch.preferred_time or "18:30",
                    booking_url="https://disneyworld.disney.go.com/dining/",
                    notes="Mock opening for a high-demand dining reservation.",
                )
            )
        elif watch.watch_type == WatchType.LIGHTNING_LANE and "tron" in normalized_name:
            openings.append(
                AvailabilityOpportunity(
                    watch_id=watch.id or 0,
                    watch_type=watch.watch_type,
                    destination=watch.destination,
                    item_name=watch.item_name,
                    available_date=max(watch.start_date, date.today().isoformat()),
                    available_time=watch.preferred_time or "10:15",
                    booking_url="https://disneyworld.disney.go.com/lightning-lane-passes/",
                    notes="Mock Lightning Lane return window.",
                )
            )
        elif watch.watch_type == WatchType.DVC and "boardwalk" in normalized_name:
            openings.append(
                AvailabilityOpportunity(
                    watch_id=watch.id or 0,
                    watch_type=watch.watch_type,
                    destination=watch.destination,
                    item_name=watch.item_name,
                    available_date=watch.start_date,
                    available_time="check-in",
                    booking_url="https://disneyvacationclub.disney.go.com/",
                    notes="Mock DVC room-night availability.",
                )
            )

        return openings


def opportunity_to_json(opportunity: AvailabilityOpportunity) -> dict[str, object]:
    """Serialize an opportunity for API responses."""

    data = asdict(opportunity)
    data["watch_type"] = opportunity.watch_type.value
    return data
