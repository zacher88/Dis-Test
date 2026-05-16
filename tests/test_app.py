from __future__ import annotations

import tempfile
import unittest

from disney_alerts.app import DisneyAlertsApp, display_urls
from disney_alerts.models import WatchRequest, WatchType
from disney_alerts.providers import MockAvailabilityProvider
from disney_alerts.storage import WatchStore


class DisneyAlertsTests(unittest.TestCase):
    def make_app(self) -> DisneyAlertsApp:
        database = tempfile.NamedTemporaryFile(delete=True)
        self.addCleanup(database.close)
        return DisneyAlertsApp(WatchStore(database.name), MockAvailabilityProvider())

    def test_create_watch_persists_request(self) -> None:
        app = self.make_app()
        watch = app.create_watch(
            {
                "watch_type": "dining",
                "destination": "Walt Disney World",
                "item_name": "'Ohana",
                "party_size": "4",
                "start_date": "2026-06-01",
                "end_date": "2026-06-03",
                "preferred_time": "18:00",
                "contact": "guest@example.com",
            }
        )

        self.assertIsNotNone(watch.id)
        self.assertEqual(app.store.list_watches()[0].item_name, "'Ohana")

    def test_mock_provider_finds_matching_dining_opening(self) -> None:
        provider = MockAvailabilityProvider()
        opportunities = provider.search(
            WatchRequest(
                id=10,
                watch_type=WatchType.DINING,
                destination="Walt Disney World",
                item_name="'Ohana",
                party_size=2,
                start_date="2026-06-01",
                end_date="2026-06-01",
                preferred_time="18:30",
                contact="guest@example.com",
            )
        )

        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].watch_id, 10)
        self.assertIn("dining", opportunities[0].booking_url)

    def test_check_now_saves_opportunities(self) -> None:
        app = self.make_app()
        app.create_watch(
            {
                "watch_type": "lightning_lane",
                "destination": "Magic Kingdom",
                "item_name": "TRON Lightcycle / Run",
                "party_size": "2",
                "start_date": "2026-06-01",
                "end_date": "2026-06-01",
                "preferred_time": "10:00",
                "contact": "guest@example.com",
            }
        )

        found = app.check_now()

        self.assertEqual(len(found), 1)
        self.assertEqual(len(app.store.list_opportunities()), 1)
        self.assertEqual(found[0]["watch_type"], "lightning_lane")

    def test_create_watch_validates_required_fields(self) -> None:
        app = self.make_app()

        with self.assertRaisesRegex(ValueError, "required"):
            app.create_watch({"watch_type": "dvc"})

    def test_display_urls_includes_lan_address_for_ipad_testing(self) -> None:
        urls = display_urls("0.0.0.0", 8000, ["192.168.1.25"])

        self.assertEqual(urls, ["http://127.0.0.1:8000", "http://192.168.1.25:8000"])


if __name__ == "__main__":
    unittest.main()
