from scraper_generic import *
from scraper_custom import *
import time
from dotenv import load_dotenv

load_dotenv()  # loads .env file into environment

scraped_events = []


def any_word_in(phrase: str, words: List[str]) -> bool:
    for word in words:
        if word in phrase:
            return True
    return False


# Bainbridge Township
events = scrape_ics("http://bainbridgetwp.com/events/list/?ical=1")
for event in events:
    event.event_type = "GOVERNMENT"
    event.zip_code = "44023"
scraped_events.extend(events)

# Bainbridge Library
events = scrape_ics(
    "https://geaugalibrary.libcal.com/ical_subscribe.php?src=p&cid=9901&cam=5019"
)
for event in events:
    event.event_type = "LIBRARY"
    event.zip_code = "44023"
scraped_events.extend(events)

# Kenston Schools
events = scrape_ics(
    "https://thrillshare-cmsv2.services.thrillshare.com/api/v4/o/22349/cms/events/generate_ical?filter_ids&section_ids"
)
filters = ["theater", "play", "concert", "silver bells"]
filt_events = []
for event in events:
    if any_word_in(event.name.lower(), filters):
        event.event_type = "SCHOOL"
        event.zip_code = "44023"
        filt_events.append(event)
scraped_events.extend(filt_events)

# Kenston Sports
events = scrape_ics(
    "https://mmboltapi.azurewebsites.net/api/v2/events/downloadcalendar/2482879/0"
)
filt_events = []
for event in events:
    if "vs" in event.name.lower():
        event.event_type = "SCHOOL"
        event.zip_code = "44023"
        event.url = "https://www.kenstonathletics.com/"
        filt_events.append(event)
scraped_events.extend(filt_events)

# CVCC - https://www.cvcc.org/events/calendar
timestamp_ms = int(time.time() * 1000)
url = f"https://www.cvcc.org/events_upcoming?t={timestamp_ms}&rendermode=json&version=3&limit=20"
events = scrape_json(url)
scraped_events.extend(events)

# Geauga Maple Leaf
url = "https://www.geaugamapleleaf.com/category/community/geauga-happenings/"
scraped_urls = get_geauga_maple_leaf_current_events_url(url)
events_json = extract_events_llm(
    scraped_urls[0], "/html/body/div[2]/div[2]/div[2]/div[3]"
)
events = convert_llm_json_to_events(events_json, url)
scraped_events.extend(events)

# Bainbridge Historical Society
url = "https://bainbridgehistoricalsociety.org/events/"
events = parse_bainbridge_events(url)
scraped_events.extend(events)

for event in scraped_events:
    print(event)
