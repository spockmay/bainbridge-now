"""
A Python class to represent a calendar event.
"""

from datetime import datetime
from typing import Optional
import sqlite3
from typing import List


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
                    promoted INTEGER
                )
            """
            )

            # Insert the event data
            cursor.execute(
                """
                INSERT INTO events (name, start_datetime, end_datetime, url, event_type, zip_code, promoted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

            conn.commit()
            print(f"Successfully wrote event '{self.name}' to the database.")

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
            SELECT name, start_datetime, end_datetime, url, event_type, zip_code, promoted
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
