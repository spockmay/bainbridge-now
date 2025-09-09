from icalendar import Calendar, Event
from typing import List
import requests

from event import Event


def scrape_ics(source: str) -> List[Event]:
    """
    Scrapes a .ics file, parses the events, and returns a list of Event objects.
    The source can be either a local file path or a URL.

    Args:
        source: The file path to the .ics file or a URL.

    Returns:
        A list of Event objects.
    """
    events = []
    ics_content = None

    try:
        if source.startswith("http"):
            if requests is None:
                return []
            print(f"Downloading from {source}...")
            response = requests.get(source)
            response.raise_for_status()  # Raise an exception for bad status codes
            ics_content = response.content
        else:
            with open(source, "rb") as f:
                ics_content = f.read()

        cal = Calendar.from_ical(ics_content)
        for component in cal.walk():
            if component.name == "VEVENT":
                # Extracting data from the VEVENT component
                start_dt = component.get("dtstart").dt
                end_dt = (
                    component.get("dtend").dt
                    if component.get("dtend")
                    else None
                )
                name = str(component.get("summary"))
                url = (
                    str(component.get("url")) if component.get("url") else None
                )
                event_type = (
                    str(component.get("categories"))
                    if component.get("categories")
                    else "UNKNOWN"
                )

                # ICS files don't have a standard ZIP code field.
                # We will try to extract it from the location or use a placeholder.
                location = (
                    str(component.get("location"))
                    if component.get("location")
                    else ""
                )
                zip_code = (
                    location.split(",")[-1].strip()
                    if location and location.split(",")[-1].strip().isdigit()
                    else "N/A"
                )

                event = Event(
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    name=name,
                    url=url,
                    event_type=event_type,
                    zip_code=zip_code,
                )
                events.append(event)
    except FileNotFoundError:
        print(f"Error: The file '{source}' was not found.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the ICS file: {e}")
    except Exception as e:
        print(f"An error occurred while parsing the ICS file: {e}")

    return events


if __name__ == "__main__":
    scraped_events = scrape_ics("http://bainbridgetwp.com/events/list/?ical=1")

    for event in scraped_events:
        print(event)
