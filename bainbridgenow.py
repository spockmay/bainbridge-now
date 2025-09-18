from scraper_generic import *
from scraper_custom import *
from datetime import timedelta, datetime
from dotenv import load_dotenv
from event import *
import time

load_dotenv()  # loads .env file into environment


def get_upcoming_friday():
    today = datetime.now()
    # Calculate the number of days until the next Friday (Friday is weekday 4)
    days_until_friday = (4 - today.weekday() + 7) % 7
    if days_until_friday == 0:
        # If today is Friday, the next Friday is in 7 days
        days_until_friday = 0

    upcoming_friday = today + timedelta(days=days_until_friday)
    # Set the time to midnight (start of the day)
    return upcoming_friday.replace(hour=0, minute=0, second=0, microsecond=0)


def any_word_in(phrase: str, words: List[str]) -> bool:
    for word in words:
        if word in phrase:
            return True
    return False


def scrape_events():
    scraped_events = []

    # Bainbridge Township
    print("Scraing Bainbridge Township Page")
    events = scrape_ics("http://bainbridgetwp.com/events/list/?ical=1")
    for event in events:
        event.event_type = "GOVERNMENT"
        event.zip_code = "44023"
    print("  %s events found." % len(events))
    scraped_events.extend(events)

    # Bainbridge Library
    print("Scraping Bainbridge Library Page")
    events = scrape_ics(
        "https://geaugalibrary.libcal.com/ical_subscribe.php?src=p&cid=9901&cam=5019"
    )
    for event in events:
        event.event_type = "LIBRARY"
        event.zip_code = "44023"
    print("  %s events found." % len(events))
    scraped_events.extend(events)

    # Kenston Schools
    print("Scraping Kenston Schools Page")
    events = scrape_ics(
        "https://thrillshare-cmsv2.services.thrillshare.com/api/v4/o/22349/cms/events/generate_ical?filter_ids&section_ids"
    )
    filters = [
        "theater",
        "play",
        "concert",
        "silver bells",
        "board of education",
    ]
    filt_events = []
    for event in events:
        if any_word_in(event.name.lower(), filters):
            event.event_type = "SCHOOL"
            event.zip_code = "44023"
            filt_events.append(event)
    print("  %s events found." % len(filt_events))
    scraped_events.extend(filt_events)

    # Kenston Sports
    print("Scraping Kenston Athletics Page")
    events = scrape_ics(
        "https://mmboltapi.azurewebsites.net/api/v2/events/downloadcalendar/2482879/0"
    )
    filt_events = []
    for event in events:
        if "vs" in event.name.lower():
            event.event_type = "SPORTS"
            event.zip_code = "44023"
            event.url = "https://www.kenstonathletics.com/"
            filt_events.append(event)
    print("  %s events found." % len(filt_events))
    scraped_events.extend(filt_events)

    # CVCC - https://www.cvcc.org/events/calendar
    print("Scraping CVCC Page")
    timestamp_ms = int(time.time() * 1000)
    url = f"https://www.cvcc.org/events_upcoming?t={timestamp_ms}&rendermode=json&version=3&limit=20"
    events = scrape_json(url)
    print("  %s events found." % len(events))
    scraped_events.extend(events)

    # Geauga Maple Leaf
    print("Scraping Geauga Maple Leaf")
    url = (
        "https://www.geaugamapleleaf.com/category/community/geauga-happenings/"
    )
    scraped_urls = get_geauga_maple_leaf_current_events_url(url)
    events_json = extract_events_llm(
        scraped_urls[0], "/html/body/div[2]/div[2]/div[2]/div[3]"
    )
    events = convert_llm_json_to_events(events_json, url)
    print("  %s events found." % len(events))
    scraped_events.extend(events)

    # Bainbridge Historical Society
    print("Scraping Bainbridge Historical Society")
    url = "https://bainbridgehistoricalsociety.org/events/"
    events = parse_bainbridge_events(url)
    print("  %s events found." % len(events))
    scraped_events.extend(events)

    # Geauga County Parks
    print("Scraping Geauga County Parks")
    events = scrape_park_events()
    events.extend(scrape_park_events(pg=2))
    events.extend(scrape_park_events(pg=3))
    print("  %s events found." % len(events))
    scraped_events.extend(events)

    # Chagrin Falls Merchant Assoc
    print("Scraping Geauga County Parks")
    events = scrape_merchat_assoc_events()
    print("  %s events found." % len(events))
    scraped_events.extend(events)

    print("Writing to database...")
    for event in scraped_events:
        event.write_to_db()
    print("Done!")


def get_unique_event_types() -> List[str]:
    """
    Connects to an SQLite database, gets all unique values from the 'event_type'
    column in the specified table, and returns them as a list.

    Args:
        db_path (str): The file path to the SQLite database.
        table_name (str): The name of the table to query.

    Returns:
        list: A list of unique event types. Returns an empty list if an
              error occurs.
    """
    conn = None
    try:
        conn = sqlite3.connect("event_db.sql")
        cursor = conn.cursor()

        query = f"SELECT DISTINCT event_type FROM events;"

        cursor.execute(query)
        results = cursor.fetchall()
        unique_event_types = [row[0] for row in results]
        return unique_event_types

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        # Ensure the database connection is closed, even if an error occurred
        if conn:
            conn.close()


# scrape_events()

event_types = get_unique_event_types()
out_html = "<html>"

for event_type in event_types:
    upcoming = get_events_by_date_and_type(
        get_upcoming_friday(),
        get_upcoming_friday() + timedelta(days=8),
        event_type=event_type,
    )

    if upcoming:
        out_html += "<h1>%s Events:</h1>" % (event_type.capitalize(),)
        for event in upcoming:
            out_html += event.html()

out_html += "</html>"
try:
    with open("output.html", "w") as html_file:
        # Write the contents of the out_html string to the file.
        html_file.write(out_html)
    print(f"Successfully wrote the HTML content to file")
except IOError as e:
    # Handle potential file writing errors.
    print(f"An error occurred while writing to the file: {e}")
