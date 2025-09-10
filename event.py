"""
A Python class to represent a calendar event.
"""

from datetime import datetime
from typing import Optional
import sqlite3
from typing import List
import pytz


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
        notes: str = "",
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.name = name
        self.url = url
        self.event_type = event_type
        self.zip_code = zip_code
        self.promoted = promoted
        self.notes = notes

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
            f"URL: '{self.url}', Promoted: '{self.promoted}', Notes: '{self.notes}')"
        )

    def html(self) -> str:
        """
        Returns an HTML formatted version of the event
        """
        # Define the target timezone
        nyc_tz = pytz.timezone("America/New_York")

        # 1. Convert the start_datetime to the America/New York timezone
        # If the original datetime is naive, localize it.
        if (
            self.start_datetime.tzinfo is None
            or self.start_datetime.tzinfo.utcoffset(self.start_datetime)
            is None
        ):
            # This assumes the original naive datetime is in the system's local timezone.
            local_tz = pytz.timezone(
                "America/New_York"
            )  # Or get the system timezone
            start_datetime_aware = local_tz.localize(self.start_datetime)
        else:
            start_datetime_aware = self.start_datetime.astimezone(nyc_tz)

        # Format the datetimes for display
        start_time_str = start_datetime_aware.strftime("%B %d, %Y, %#I:%M %p")

        if self.end_datetime:
            if (
                self.end_datetime.tzinfo is None
                or self.end_datetime.tzinfo.utcoffset(self.end_datetime)
                is None
            ):
                local_tz = pytz.timezone("America/New_York")
                end_datetime_aware = local_tz.localize(self.end_datetime)
            else:
                end_datetime_aware = self.end_datetime.astimezone(nyc_tz)

            # 4. Format the end time string
            end_time_str = " - %s" % (end_datetime_aware.strftime("%I:%M %p"))
        else:
            end_time_str = ""

        # Construct the time range string
        time_range = start_time_str
        if self.end_datetime:
            time_range = f"{start_time_str.split(',')[0]}, {start_time_str.split(',')[1].strip()} @ {start_time_str.split(',')[2].strip()} {end_time_str}"

        notes_html = (
            f"<br><strong>Notes:</strong> {self.notes}</br>"
            if self.notes
            else ""
        )

        return f"""
            <div>
                <h2>{self.name}</h2>
                <p>{time_range}
                <br>{self.zip_code}
                {notes_html}
                <br><a href="{self.url}" target="_blank">details</a></p>
            </div>
        """

    def write_to_db(self, db_path: str = "event_db.sql"):
        """
        Writes the event object's data to a SQLite database.

        Args:
            db_path: The file path to the SQLite database.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create the events table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    start_datetime TEXT,
                    end_datetime TEXT,
                    url TEXT,
                    event_type TEXT,
                    zip_code TEXT,
                    promoted INTEGER,
                    notes TEXT
                )
            """
            )

            # Insert the event data
            cursor.execute(
                """
                INSERT INTO events (name, start_datetime, end_datetime, url, event_type, zip_code, promoted, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.name,
                    self.start_datetime.isoformat(),
                    (
                        self.end_datetime.isoformat()
                        if self.end_datetime
                        else None
                    ),
                    self.url,
                    self.event_type,
                    self.zip_code,
                    self.promoted,
                    self.notes,
                ),
            )

            conn.commit()

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            if conn:
                conn.close()


def get_events_by_date_and_type(
    start_date: datetime,
    end_date: datetime,
    event_type: Optional[str] = None,
    db_path: str = "event_db.sql",
) -> List[Event]:
    """
    Retrieves events from the SQLite database that fall within a given date range
    and optionally match a specific event type.

    Args:
        db_path: The file path to the SQLite database.
        start_date: The start date for the query range.
        end_date: The end date for the query range.
        event_type: The optional type of event to filter by. If None, all event types will be returned.

    Returns:
        A list of Event objects that match the criteria.
    """
    events = []
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # The dates in the database are stored as ISO format strings, so we convert the
        # input dates to strings for comparison.
        base_query = """
            SELECT name, start_datetime, end_datetime, url, event_type, zip_code, promoted, notes
            FROM events
            WHERE start_datetime >= ? AND start_datetime <= ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        # Dynamically build the query based on whether event_type is provided
        if event_type:
            query = base_query + " AND event_type = ?"
            params.append(event_type)
        else:
            query = base_query

        query += " ORDER BY start_datetime"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        for row in rows:
            (
                name,
                start_dt_str,
                end_dt_str,
                url,
                event_type,
                zip_code,
                promoted,
                notes,
            ) = row
            start_dt = datetime.fromisoformat(start_dt_str)
            end_dt = datetime.fromisoformat(end_dt_str) if end_dt_str else None

            event = Event(
                start_datetime=start_dt,
                end_datetime=end_dt,
                name=name,
                url=url,
                event_type=event_type,
                zip_code=zip_code,
                promoted=bool(promoted),
                notes=notes,
            )
            events.append(event)

    except sqlite3.Error as e:
        print(f"SQLite error while querying: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

    return events
