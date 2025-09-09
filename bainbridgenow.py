from scraper_generic import scrape_ics
from scraper_custom import scrape_json
from event import Event
import time

scraped_events = []

# Bainbridge Township
events = scrape_ics("http://bainbridgetwp.com/events/list/?ical=1")
for event in events:
    event.event_type = "GOVERNMENT"
    event.zip_code = "44023"
scraped_events.append(events)

# Bainbridge Library
events = scrape_ics(
    "https://geaugalibrary.libcal.com/ical_subscribe.php?src=p&cid=9901&cam=5019"
)
for event in events:
    event.event_type = "LIBRARY"
    event.zip_code = "44023"
scraped_events.append(events)

# CVCC - https://www.cvcc.org/events/calendar
timestamp_ms = int(time.time() * 1000)
url = f"https://www.cvcc.org/events_upcoming?t={timestamp_ms}&rendermode=json&version=3&limit=20"
scraped_events = scrape_json(url)

for event in scraped_events:
    print(event)
