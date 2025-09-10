"""
A Python class to represent a calendar event.
"""

from datetime import datetime
from typing import Optional


class Event:
    """
    Represents an event with details such as start time, name, and location.

    Attributes:
        start_datetime (datetime): The starting date and time of the event.
        name (str): The name of the event.
        event_type (str): The type or category of the event (e.g., 'government', 'parks').
        zip_code (str): The ZIP code where the event is located.
        end_datetime (Optional[datetime]): The optional ending date and time of the event.
        url (Optional[str]): An optional URL for more information about the event.
        promoted (bool): Is this event to be displayed as promoted? Defaults to false.
    """

    def __init__(
        self,
        start_datetime: datetime,
        name: str,
        event_type: str,
        zip_code: str,
        end_datetime: Optional[datetime] = None,
        url: Optional[str] = None,
        promoted: bool = False,
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.name = name
        self.url = url
        self.event_type = event_type
        self.zip_code = zip_code
        self.promoted = promoted

    def __repr__(self):
        """
        Provides a string representation of the Event object for easy debugging.
        """
        end_time_str = (
            f", End: {self.end_datetime.strftime('%Y-%m-%d %H:%M')}"
            if self.end_datetime
            else ""
        )
        return (
            f"Event(Name: '{self.name}', Start: {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"
            f"{end_time_str}, Type: '{self.event_type}', Zip: '{self.zip_code}', "
            f"URL: '{self.url}', Promoted: '{self.promoted}')"
        )
