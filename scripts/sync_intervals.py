"""Read-only Intervals export. Credentials come exclusively from environment."""

import base64
import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RUN_TYPES = {"Run", "TrailRun", "VirtualRun"}


def get_json(path, key):
    token = base64.b64encode(f"API_KEY:{key}".encode()).decode()
    request = Request("https://intervals.icu/api/v1" + path, headers={
        "Authorization": f"Basic {token}", "Accept": "application/json",
        "User-Agent": "EuanRunningDashboard/1.0",
    })
    for attempt in range(4):
        try:
            with urlopen(request, timeout=60) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                # Deliberately do not include response bodies, headers or credentials.
                raise RuntimeError(f"Intervals request failed: HTTP {error.code}") from None
        except (URLError, TimeoutError):
            if attempt == 3:
                raise RuntimeError("Intervals request failed: connection or timeout") from None
        time.sleep(2 ** (attempt + 1))


def encode_route(streams):
    """Intervals latlng uses data=latitudes, data2=longitudes."""
    stream = next((s for s in streams if s.get("type") == "latlng"), {})
    latitudes, longitudes = stream.get("data", []), stream.get("data2", [])
    if not isinstance(latitudes, list) or not isinstance(longitudes, list):
        raise ValueError("Unexpected latlng stream format")
    if len(latitudes) != len(longitudes):
        raise ValueError("Latitude and longitude lengths differ")
    points = []
    for lat, lon in zip(latitudes, longitudes):
        if lat is None or lon is None:
            continue
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            continue
        if math.isfinite(lat) and math.isfinite(lon) and abs(lat) <= 90 and abs(lon) <= 180:
            point = (math.floor(lat * 100000 + 0.5), math.floor(lon * 100000 + 0.5))
            if not points or point != points[-1]:
                points.append(point)
    if len(points) < 2:
        return None
    result, previous = [], (0, 0)
    for point in points:
        for current, last in zip(point, previous):
            delta = current - last
            value = ~(delta << 1) if delta < 0 else delta << 1
            while value >= 32:
                result.append(chr((32 | (value & 31)) + 63))
                value >>= 5
            result.append(chr(value + 63))
        previous = point
    return "".join(result)


def number(value, default=0):
    if value is None:
        return default
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError("Invalid activity metric")
    return value


def normalize(activity, route):
    local = activity["start_date_local"]
    datetime.fromisoformat(local)
    seconds = round(number(activity.get("moving_time")))
    distance = number(activity.get("distance"))
    return {
        # Keep the original ID string: avoids collisions across i-prefixed IDs.
        "run_id": str(activity["id"]), "name": "Run",
        "distance": distance,
        "moving_time": f"{seconds // 3600}:{seconds % 3600 // 60:02}:{seconds % 60:02}",
        "type": "Run", "subtype": activity["type"],
        "start_date": activity.get("start_date") or local,
        "start_date_local": local, "location_country": None,
        "summary_polyline": route, "average_heartrate": None,
        "average_speed": distance / seconds if seconds else 0,
        "elevation_gain": activity.get("total_elevation_gain"),
        "source": "Intervals.icu", "streak": 0,
    }


def export(fetch, athlete, routes=True, start="2000-01-01"):
    date.fromisoformat(start)
    query = urlencode({"oldest": start, "newest": (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()})
    raw = fetch(f"/athlete/{quote(athlete, safe='')}/activities?{query}")
    if not isinstance(raw, list):
        raise ValueError("Expected an activities array")
    result, skipped = {}, 0
    for activity in raw:
        if not activity.get("type"):
            skipped += 1  # Intervals returns stubs for Strava-only activities.
            continue
        if activity["type"] not in RUN_TYPES:
            continue
        route = None
        if routes and "latlng" in (activity.get("stream_types") or []):
            route = encode_route(fetch(f"/activity/{quote(str(activity['id']), safe='')}/streams.json?types=latlng"))
            time.sleep(0.65)  # Stay below 100 requests/minute; retry transient limits.
        row = normalize(activity, route)
        result[row["run_id"]] = row
    return sorted(result.values(), key=lambda a: a["start_date_local"], reverse=True), skipped


def main():
    key = os.environ.get("INTERVALS_ICU_API_KEY")
    athlete = os.environ.get("INTERVALS_ICU_ATHLETE_ID")
    if not key or not athlete:
        raise RuntimeError("Set INTERVALS_ICU_API_KEY and INTERVALS_ICU_ATHLETE_ID in GitHub Secrets")
    routes = os.environ.get("PUBLISH_ROUTES", "true").lower() == "true"
    activities, skipped = export(lambda p: get_json(p, key), athlete, routes, os.environ.get("SYNC_START_DATE", "2000-01-01"))
    if skipped:
        print(f"Warning: {skipped} unavailable activity stubs skipped. For complete data, export directly from HealthFit to Intervals.icu.")
    # A failed/empty import must never replace a working public history silently.
    if not activities:
        raise RuntimeError("No accessible runs found; existing deployment is preserved")
    target = ROOT / "src/static/activities.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(activities, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    temporary.replace(target)
    (ROOT / "src/static/sync-status.json").write_text(json.dumps({
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "runs": len(activities), "routes": routes, "skipped_stubs": skipped,
    }) + "\n", encoding="utf-8")
    print(f"Exported {len(activities)} runs, {sum(bool(a['summary_polyline']) for a in activities)} GPS routes")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"Sync stopped: {error}", file=sys.stderr)
        sys.exit(1)
