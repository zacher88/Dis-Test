"""Standard-library web app for Disney availability alerts."""

from __future__ import annotations

import argparse
import json
import os
import socket
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .alerts import ConsoleAlertService
from .models import WatchRequest, WatchType
from .providers import AvailabilityProvider, MockAvailabilityProvider, opportunity_to_json
from .storage import WatchStore

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
TEMPLATE_DIR = ROOT / "templates"


class DisneyAlertsApp:
    """Coordinates storage, inventory providers, and alert delivery."""

    def __init__(
        self,
        store: WatchStore,
        provider: AvailabilityProvider | None = None,
        alerts: ConsoleAlertService | None = None,
    ) -> None:
        self.store = store
        self.provider = provider or MockAvailabilityProvider()
        self.alerts = alerts or ConsoleAlertService()

    def create_watch(self, payload: dict[str, object]) -> WatchRequest:
        watch = WatchRequest(
            id=None,
            watch_type=WatchType(str(payload.get("watch_type", WatchType.DINING.value))),
            destination=str(payload.get("destination", "Walt Disney World")).strip(),
            item_name=str(payload.get("item_name", "")).strip(),
            party_size=int(payload.get("party_size", 1)),
            start_date=str(payload.get("start_date", "")).strip(),
            end_date=str(payload.get("end_date", payload.get("start_date", ""))).strip(),
            preferred_time=str(payload.get("preferred_time", "")).strip(),
            contact=str(payload.get("contact", "")).strip(),
        )
        self._validate_watch(watch)
        return self.store.add_watch(watch)

    def check_now(self) -> list[dict[str, object]]:
        all_opportunities = []
        for watch in self.store.list_watches():
            opportunities = self.provider.search(watch)
            self.store.save_opportunities(opportunities)
            for opportunity in opportunities:
                self.alerts.send(watch, opportunity)
            all_opportunities.extend(opportunities)
        return [opportunity_to_json(opportunity) for opportunity in all_opportunities]

    @staticmethod
    def _validate_watch(watch: WatchRequest) -> None:
        if not watch.item_name:
            raise ValueError("Restaurant, attraction, or resort name is required.")
        if watch.party_size < 1:
            raise ValueError("Party size must be at least 1.")
        if not watch.start_date or not watch.end_date:
            raise ValueError("Start and end dates are required.")
        if not watch.contact:
            raise ValueError("An alert contact is required.")


def make_handler(app: DisneyAlertsApp) -> type[SimpleHTTPRequestHandler]:
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - required by http.server
            path = urlparse(self.path).path
            if path == "/":
                self._send_file(TEMPLATE_DIR / "index.html", "text/html; charset=utf-8", TEMPLATE_DIR)
            elif path == "/api/watchlist":
                watches = [watch.__dict__ | {"watch_type": watch.watch_type.value} for watch in app.store.list_watches()]
                self._send_json(watches)
            elif path == "/api/opportunities":
                opportunities = [opportunity_to_json(item) for item in app.store.list_opportunities()]
                self._send_json(opportunities)
            elif path.startswith("/static/"):
                self._send_file(STATIC_DIR / path.removeprefix("/static/"), self._content_type(path), STATIC_DIR)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:  # noqa: N802 - required by http.server
            path = urlparse(self.path).path
            try:
                if path == "/api/watchlist":
                    watch = app.create_watch(self._read_json())
                    self._send_json(watch.__dict__ | {"watch_type": watch.watch_type.value}, HTTPStatus.CREATED)
                elif path == "/api/check":
                    self._send_json(app.check_now())
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except ValueError as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None:
            if os.environ.get("DISNEY_ALERTS_DEBUG"):
                super().log_message(format, *args)

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            return json.loads(raw)

        def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, file_path: Path, content_type: str, allowed_root: Path) -> None:
            resolved_path = file_path.resolve()
            resolved_root = allowed_root.resolve()
            if not resolved_path.is_file() or resolved_root not in resolved_path.parents:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            body = resolved_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        @staticmethod
        def _content_type(path: str) -> str:
            if path.endswith(".css"):
                return "text/css; charset=utf-8"
            if path.endswith(".js"):
                return "text/javascript; charset=utf-8"
            return "application/octet-stream"

    return Handler


def get_lan_addresses() -> list[str]:
    """Return likely LAN IPv4 addresses for testing from another device."""

    addresses: set[str] = set()
    try:
        host_results = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    except OSError:
        host_results = []

    for result in host_results:
        address = result[4][0]
        if not address.startswith("127."):
            addresses.add(address)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("8.8.8.8", 80))
            address = probe.getsockname()[0]
        except OSError:
            address = ""
        if address and not address.startswith("127."):
            addresses.add(address)

    return sorted(addresses)


def display_urls(host: str, port: int, lan_addresses: list[str] | None = None) -> list[str]:
    """Build URLs to show in the console when the server starts."""

    if host in {"0.0.0.0", "::", ""}:
        addresses = [
            "127.0.0.1",
            *(lan_addresses if lan_addresses is not None else get_lan_addresses()),
        ]
    else:
        addresses = [host]
    return [f"http://{address}:{port}" for address in dict.fromkeys(addresses)]


def run(host: str = "127.0.0.1", port: int = 8000, database: str = "disney_alerts.db") -> None:
    app = DisneyAlertsApp(WatchStore(database))
    server = ThreadingHTTPServer((host, port), make_handler(app))
    print("Disney Alerts running. Open:", flush=True)
    for url in display_urls(host, port):
        print(f"  {url}", flush=True)
    if host == "0.0.0.0":
        print("Use a LAN URL above from an iPad on the same Wi-Fi network.", flush=True)
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Disney availability alert web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--database", default="disney_alerts.db")
    args = parser.parse_args()
    run(args.host, args.port, args.database)


if __name__ == "__main__":
    main()
