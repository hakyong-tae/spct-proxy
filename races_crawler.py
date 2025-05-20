import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

BASE_URL = "https://time.spct.kr"
LIST_URL = f"{BASE_URL}/main.php"

def fetch_event_list():
    print("Fetching event list...")
    response = requests.get(LIST_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    events = []

    table_rows = soup.select("tbody tr")
    print("Found rows:", len(table_rows))

    for row in table_rows:
        tds = row.find_all("td")
        if len(tds) < 3:
            continue

        date_text = tds[1].get_text(strip=True)
        link = tds[2].find("a")
        if not link:
            continue

        title = link.get_text(strip=True)
        href = link.get("href")

        if "&currentPage=" in href:
            href = href.split("&currentPage=")[0]

        event_url = f"{BASE_URL}/{href}"

        event_no = None
        if "EVENT_NO=" in href:
            event_no = href.split("EVENT_NO=")[1]

        event = {
            "event_no": event_no,
            "date": date_text,
            "title": title,
            "url": event_url
        }
        events.append(event)

    return events

def save_events(events):
    output_path = os.path.join(os.path.dirname(__file__), "spct_races_parsed.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(events)} events to {output_path}")

if __name__ == "__main__":
    events = fetch_event_list()
    save_events(events)
