from datetime import datetime
from typing import List
import json
import re
import requests
from lxml import html
from bs4 import BeautifulSoup

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
                event_type = "COMMUNITY"

                event = Event(
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    name=name,
                    url=url,
                    event_type=event_type,
                    zip_code=zip_code,
                )

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


def parse_datetime(date_str):
    """
    Converts a date string like "Wednesday, September 10, 2025 @ 7pm"
    into ISO 8601 format.
    """
    # Remove weekday dynamically
    if "," in date_str:
        date_str = date_str.split(",", 1)[
            1
        ].strip()  # " September 10, 2025 @ 7pm"

    date_str = date_str.replace("@", "").strip()  # "September 10, 2025 7pm"

    dt = datetime.strptime(date_str, "%B %d, %Y %I%p")
    return dt.isoformat()


def parse_bainbridge_events(url: str) -> List[Event]:
    # This method parses the events from the Bainbridge Historical Society webpage
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    container = tree.xpath("/html/body/div/div[2]/div/main/article/div/div")
    if not container:
        raise ValueError("Event container not found.")
    container = container[0]

    events = []
    children = container.getchildren()
    i = 0
    while i < len(children):
        el = children[i]

        if el.text_content().strip().startswith("PAST EVENT"):
            break

        if el.tag == "h4" and "center" not in el.get("style", ""):
            title = el.text_content().strip()
            if title == "":
                i += 1
                continue
            i += 1

            # First <p> after title: start datetime
            start_datetime = None
            if i < len(children) and children[i].tag == "p":
                try:
                    start_datetime = parse_datetime(
                        children[i].text_content().strip()
                    )
                except Exception:
                    start_datetime = None
                i += 1

            # Second <p> after title: contains subtitle (bold) + description
            if i < len(children) and children[i].tag == "p":
                second_p = children[i]
                # Find <strong> inside second <p> for subtitle
                subtitle_el = second_p.xpath(".//b")
                if subtitle_el:
                    subtitle = (
                        subtitle_el[0].text_content().strip().split(".")[0]
                    )
                    title = f"{title}: {subtitle}"  # append subtitle to title
                i += 1

            event = Event(
                start_datetime=start_datetime,
                name=title,
                url=url,
                event_type="COMMUNITY",
                zip_code="44023",
            )
            events.append(event)
        else:
            i += 1

    return events


def scrape_park_events(pg: int = 1) -> List[Event]:
    base_url = "https://reservations.geaugaparkdistrict.org"

    if pg == 1:
        url = f"{base_url}/programs/"
    else:
        index = 25 * (pg - 1)
        url = f"{base_url}/programs/index.shtml?month=&day=&year=&list_programs=1&or=&dts=&wy=asc&num={index}&sid=885364.17254&uid="

    response = requests.get(url)
    response.raise_for_status()  # raises error if request failed
    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    # Locate the main event table
    table = soup.find("table", attrs={"width": "688", "bgcolor": "white"})
    if not table:
        return events

    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) <= 8:
            continue

        # Name + URL
        link = cols[2].find("a")
        name = link.get_text(strip=True) if link else None
        url = base_url + link["href"] if link and link.get("href") else None

        # Location
        location = cols[3].get_text(strip=True)

        # Date
        date_str = cols[4].get_text(strip=True)

        # Time (number + AM/PM in separate columns)
        time_str = (
            cols[5].get_text(strip=True) + " " + cols[6].get_text(strip=True)
        )
        time_str = time_str.strip()

        start_datetime = None
        if date_str and time_str.strip():
            for fmt in ("%m/%d/%y %I:%M %p", "%m/%d/%y %I %p"):
                try:
                    start_datetime = datetime.strptime(
                        f"{date_str} {time_str}", fmt
                    )
                    break
                except ValueError:
                    continue
        if start_datetime is None:
            continue

        # Fee
        fee = cols[7].get_text(strip=True)

        # Availability
        availability = cols[8].get_text(strip=True)

        if availability == "Waiting list":
            continue
        if availability == "OPEN" or availability == "":
            notes = "%s" % (fee)
        else:
            notes = "%s - %s seats remaining" % (fee, availability)

        event = Event(
            start_datetime=start_datetime,
            name=name,
            url=url,
            event_type="PARK",
            zip_code=location,
            notes=notes,
        )
        events.append(event)

    return events


if __name__ == "__main__":
    events = scrape_park_events()
    events.extend(scrape_park_events(pg=2))
    events.extend(scrape_park_events(pg=3))

    for e in events:
        print(e)

    print(len(events))
