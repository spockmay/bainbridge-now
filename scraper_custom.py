from datetime import datetime
from typing import List
import json
import re
import requests
import time
from lxml import html

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


def get_geauga_maple_leaf_current_events_url(url: str) -> List[str]:
    """
    Scrapes the Geauga Maple Leaf website and extracts article URLs using lxml and XPath.

    Args:
        url: The URL of the Geauga Maple Leaf page to scrape.

    Returns:
        A list of URLs found on the page.
    """
    urls = []
    if requests is None or html is None:
        return urls

    try:
        print(f"Downloading and parsing HTML from {url}...")
        response = requests.get(url)
        response.raise_for_status()

        # Parse the HTML content using lxml
        tree = html.fromstring(response.content)

        # Use XPath to find all <a> tags within the specified path
        xpath_query = "/html/body/div[2]/div[2]/div[2]/div[1]/div/h2/a"
        links = tree.xpath(xpath_query)

        # Extract the 'href' attribute from each found element
        for link in links:
            urls.append(link.get("href"))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the webpage: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return urls


if __name__ == "__main__":
    # Scrape URLs from the Geauga Maple Leaf website
    url_geauga = (
        "https://www.geaugamapleleaf.com/category/community/geauga-happenings/"
    )
    scraped_urls = get_geauga_maple_leaf_current_events_url(url_geauga)

    if scraped_urls:
        print(
            f"Successfully scraped {len(scraped_urls)} URLs from the Geauga Maple Leaf website."
        )
        for url in scraped_urls:
            print(url)
    else:
        print("No URLs were scraped from the Geauga Maple Leaf website.")
