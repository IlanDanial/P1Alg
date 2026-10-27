"""Download Florida sailings from Carnival's public search into data/sailings.csv.

Builds the request the same way as Cruise Finder's collector (URL, query,
Accept header, MMYYYY month code) and follows every page the response reports
in results.lastPage. One request every few seconds keeps the load polite.
Then builds the quote windows, runs refresh_days, and prints the case study.

Run: python fetch_sailings.py   (about a minute; needs network access)
"""

import csv
import json
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from refresh_days import refresh_days, windows

URL = "https://www.carnival.com/cruisesearch/api/search"
QUERY = {
    "pagesize": "200",
    "numadults": "2",
    "port": "MIA,PCV,TPA,JAX",
    "sort": "fromprice",
    "showBest": "true",
    "async": "true",
    "client": "cruisesearch",
}
MONTHS = [date(2026, m, 1) for m in (11, 12)] + [date(2027, m, 1) for m in (1, 2, 3, 4)]
TODAY = date(2026, 10, 26)
C = 2  # booking closes this many days before departure (assumption)
PAUSE_S = 3
DATA = Path(__file__).parent / "data" / "sailings.csv"
FIELDS = ["sailing_id", "ship", "port", "itinerary", "departure", "nights"]


def fetch_page(month, page):
    query = QUERY | {"pagenumber": str(page), "dates": month.strftime("%m%Y")}
    req = Request(f"{URL}?{urlencode(query)}", headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))["results"]


def fetch_month(month):
    rows, page, last = [], 1, 1
    while page <= last:
        if page > 1:
            time.sleep(PAUSE_S)
        res = fetch_page(month, page)
        last = res["lastPage"]
        for it in res["itineraries"]:
            for s in it["sailings"]:
                dep = date.fromisoformat(s["departureDate"][:10])
                arr = date.fromisoformat(s["arrivalDate"][:10])
                if (arr - dep).days != it["dur"]:
                    raise ValueError(f"sailing {s['sailingId']}: dur disagrees with dates")
                rows.append({"sailing_id": s["sailingId"], "ship": it["shipName"],
                             "port": it["departurePortCode"], "itinerary": it["itineraryTitle"],
                             "departure": dep, "nights": it["dur"]})
        print(f"{month:%m/%Y} page {page}/{last}: {len(res['itineraries'])} itineraries")
        page += 1
    return rows


def read_sailings():
    with open(DATA) as f:
        return [{**r, "departure": date.fromisoformat(r["departure"]), "nights": int(r["nights"])}
                for r in csv.DictReader(f)]


def case_study():
    """Print n, m, the chosen dates and the horizon for the saved sailings."""
    sailings = read_sailings()
    iv = windows(sailings, TODAY, C)
    days, wit = refresh_days(iv)
    horizon = max(b for _, b in iv) + 1
    print(f"sailings={len(sailings)}  windows n={len(iv)}  batches m={len(days)}  "
          f"horizon={horizon} days")
    print("refresh on:", ", ".join(str(TODAY + timedelta(days=t)) for t in days))
    print("witnesses:", [(str(TODAY + timedelta(days=a)), str(TODAY + timedelta(days=b)))
                         for a, b in wit])


if __name__ == "__main__":
    rows = []
    for i, m in enumerate(MONTHS):
        if i:
            time.sleep(PAUSE_S)
        rows += fetch_month(m)
    if not rows:
        raise SystemExit("no sailings returned")
    DATA.parent.mkdir(exist_ok=True)
    with open(DATA, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["departure"], r["sailing_id"])))
    case_study()
