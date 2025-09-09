from datetime import datetime
from typing import List
import json
import re
import requests
import time

from event import Event


def scrape_json(url: str) -> List[Event]:
    """
    Scrapes events from a JSON source and returns a list of Event objects.

    Args:
        url: The URL to the JSON data.

    Returns:
        A list of Event objects.
    """
    events = []
    try:
        if requests is None:
            return []
        print(f"Downloading and parsing JSON from {url}...")
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()

        # The events are now under the 'Data' key
        for item in json_data.get("Data", []):
            try:
                # Extracting data from the JSON item
                start_dt = datetime.fromisoformat(item.get("StartDate"))
                end_dt_str = item.get("EndDate")
                end_dt = (
                    datetime.fromisoformat(end_dt_str) if end_dt_str else None
                )
                name = item.get("Name", "No Title")
                url = item.get("URL")

                # Extract zip code from the 'Location' field
                location = item.get("Location", "")
                if location is not None:
                    zip_match = re.search(r"\b\d{5}\b", location)
                    zip_code = zip_match.group(0) if zip_match else "N/A"
                else:
                    zip_code = "N/A"

                # The event type is not available, so we'll use a placeholder
                event_type = "GENERAL"

                event = Event(
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    name=name,
                    url=url,
                    event_type=event_type,
                    zip_code=zip_code,
                )
                print(event)
                events.append(event)
            except Exception as e:
                print(
                    f"An error occurred while parsing an event from JSON: {e}"
                )

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the JSON data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from response: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return events


if __name__ == "__main__":
    # Scrape events from the provided URL which returns JSON
    timestamp_ms = int(time.time() * 1000)
    url = f"https://www.cvcc.org/events_upcoming?t={timestamp_ms}&rendermode=json&version=3&limit=10"
    scraped_events = scrape_json(url)
