# Disney Availability Alerts

A standard-library Python prototype for monitoring Disney planning inventory across:

- restaurant reservations,
- Lightning Lane ride-return windows, and
- Disney Vacation Club resort bookings.

The app intentionally uses a deterministic mock provider instead of scraping Disney sites. That keeps the prototype safe to run locally while leaving a clean adapter seam for future integrations with official APIs, approved partner feeds, browser automation that a user explicitly controls, or another compliant availability source.

## Why not start with scraping?

Scraping can be brittle and may violate a site's terms, trigger bot protections, or put user accounts at risk. For a production version, prioritize this order:

1. official Disney or authorized partner APIs if available to your use case,
2. user-authorized account integrations that respect rate limits and terms,
3. email/calendar/import workflows for data the user already receives,
4. scraping only after legal review, explicit user consent, careful throttling, and a plan for changes in page structure.

## Run locally

```bash
python -m disney_alerts.app --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000>.

## Test from an iPad on the same Wi-Fi

Run the server so other devices on your local network can reach it:

```bash
python -m disney_alerts.app --host 0.0.0.0 --port 8000
```

The console prints one or more URLs. Open the LAN URL from Safari on your iPad, for example:

```text
http://192.168.1.25:8000
```

If the page does not load, make sure the computer running the app and the iPad are on the same Wi-Fi network and allow Python through your firewall.

Mock searches currently return openings for sample terms such as:

- `'Ohana` for dining,
- `TRON Lightcycle / Run` for Lightning Lane, and
- `BoardWalk Villas` for DVC.

## Test

```bash
python -m unittest discover -s tests
```

## Project structure

```text
disney_alerts/
  app.py          # HTTP routes and app orchestration
  alerts.py       # alert delivery abstraction
  models.py       # dataclasses and enums
  providers.py    # provider protocol and mock availability source
  storage.py      # SQLite repository
templates/        # HTML shell
static/           # browser JavaScript and CSS
tests/            # unittest coverage
```

## Next production steps

- Add authentication and per-user watchlists.
- Replace the console alert service with email, SMS, or push notification providers.
- Add scheduled background checks with strict rate limiting.
- Implement provider adapters only for approved data sources.
- Store secrets in environment variables or a managed secret store, never in Git.
