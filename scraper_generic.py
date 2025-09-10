from icalendar import Calendar, Event
from typing import List
import requests
from datetime import datetime
from openai import OpenAI
import json
from lxml import html

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
                name = str(component.get("summary").strip())
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
                    location=location,
                )
                events.append(event)
    except FileNotFoundError:
        print(f"Error: The file '{source}' was not found.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the ICS file: {e}")
    except Exception as e:
        print(f"An error occurred while parsing the ICS file: {e}")

    return events


def fetch_event_block(url: str, xpath: str) -> str:
    """
    Fetches the webpage at the given URL and extracts the text content
    of the block defined by the XPath XPATH.
    Returns the block's text as a string.
    """
    # Fetch the page

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # raises an error if request failed

    # Parse HTML
    tree = html.fromstring(response.content)

    # Extract with XPath
    nodes = tree.xpath(xpath)

    if not nodes:
        raise ValueError("No content found at the given XPath.")

    # Convert node(s) to text (preserve formatting where possible)
    block_text = nodes[0].text_content().strip()

    return block_text


def extract_events_llm(url: str, xpath: str):
    """
    Takes a URL of an events page, asks ChatGPT to extract events,
    and returns them as structured JSON.
    """
    block_text = fetch_event_block(url, xpath)

    prompt = f"""
    The following is text from a community events webpage:

    {block_text}

    Extract all upcoming events into a JSON array.
    Each object must have the following fields:
      - start_datetime (ISO 8601 format)
      - end_datetime (ISO 8601 format)
      - title
      - url
      - zip_code (infer from city or set to null if unknown)
      - location (either the address of the name of the location of the event)
    The default timezone for all events is America/New_York.
    """

    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that extracts structured event data from webpages.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=1,
        response_format={"type": "json_object"},  # force JSON output
    )

    # Parse JSON directly (since response_format guarantees valid JSON)
    events = json.loads(response.choices[0].message.content)

    return events


def convert_llm_json_to_events(
    json_data: List[dict], page_url: str
) -> List[Event]:
    """
    Converts a list of event dictionaries from a specific JSON format to a list of Event objects.

    Args:
        json_data: A list of dictionaries, where each dictionary represents an event.

    Returns:
        A list of Event objects.
    """
    events = []
    for item in json_data.get("events", []):
        try:
            name = item.get("title", "No Title")
            url = item.get("url")
            if url is None:
                url = page_url
            zip_code = (
                str(item.get("zip_code")) if item.get("zip_code") else "N/A"
            )
            event_type = "COMMUNITY"
            location = item.get("location")

            start_dt_str = item.get("start_datetime")
            end_dt_str = item.get("end_datetime")

            start_dt = (
                datetime.fromisoformat(start_dt_str)
                if start_dt_str
                else datetime.min
            )
            end_dt = datetime.fromisoformat(end_dt_str) if end_dt_str else None

            event = Event(
                start_datetime=start_dt,
                end_datetime=end_dt,
                name=name,
                url=url,
                event_type=event_type,
                zip_code=zip_code,
                location=location,
            )
            events.append(event)
        except Exception as e:
            print(
                f"An error occurred while converting JSON to Event object: {e}"
            )

    return events


if __name__ == "__main__":
    url = "https://www.geaugamapleleaf.com/community/geauga-happenings-592/"
    events_json = extract_events_llm(
        url, "/html/body/div[2]/div[2]/div[2]/div[3]"
    )
    events = convert_llm_json_to_events(events_json, url)

    for event in events:
        print(event)
