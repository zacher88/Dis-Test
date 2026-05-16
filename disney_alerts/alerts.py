"""Alert delivery services."""

from __future__ import annotations

from .models import AvailabilityOpportunity, WatchRequest


class ConsoleAlertService:
    """Development alert service that writes alert messages to stdout."""

    def send(self, watch: WatchRequest, opportunity: AvailabilityOpportunity) -> str:
        message = (
            f"Alert for {watch.contact}: {opportunity.item_name} is available "
            f"on {opportunity.available_date} at {opportunity.available_time}. "
            f"Book at {opportunity.booking_url}"
        )
        print(message)
        return message
