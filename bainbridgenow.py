from scraper_ics import scrape_ics
from event import Event

scraped_events = []

# Bainbridge Township
events = scrape_ics("http://bainbridgetwp.com/events/list/?ical=1")
for event in events:
    event.event_type = "GOVERNMENT"
    event.zip_code = "44023"
scraped_events.append(events)

for event in scraped_events:
    print(event)
