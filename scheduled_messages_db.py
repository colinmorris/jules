import datetime
import sqlite3

import date_utils

DB_FNAME = 'scheduled_messages.db'


class TimeTravelException(Exception):
    pass


class ScheduledMessagesDatabase(object):
    """Record of scheduled messages backed by a local sqlite db.
    """

    def __init__(self):
        """Connect to local db. If it doesn't exist, create it along with the necessary table(s).
        """
        self.conn = sqlite3.connect(DB_FNAME)
        # Create table if it doesn't exist
        # NB: "when" is a reserved keyword, hence why we call the column "wen" instead :|
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id TEXT PRIMARY KEY,
                wen DATETIME NOT NULL,
                topic TEXT NOT NULL,
                sent BOOLEAN DEFAULT FALSE
            )
        """)

    def add_scheduled_message(self, id, when, topic):
        """Record scheduled message with given params.

        Args:
            id: tool call id returned by llm, e.g. "call_9pw1qnYScqvGrCH58HWCvFH6"
            when: datetime string, e.g. "09/22/24 14:00:00"
            topic: topic of message, e.g. "Check up on user"
        """
        dt = date_utils.parse_timestring(when)
        if dt < datetime.datetime.now():
            raise TimeTravelException()

        # Insert message details into the table
        self.conn.execute(
            "INSERT INTO scheduled_messages (id, wen, topic) VALUES (?, ?, ?)", (id, dt, topic)
        )
        self.conn.commit()  # Commit changes to the database

    def mark_message_sent(self, id):
        """Mark the "sent" flag to true for message with given id.

        Args:
            id: id of the message to mark as sent
        """
        # Update the sent flag for the specific message
        self.conn.execute(
            "UPDATE scheduled_messages SET sent = 1 WHERE id = ?", (id,)
        )
        self.conn.commit()

    def get_pending_messages(self):
        """Return all messages where scheduled time < now and sent is false.

        Returns:
            List of dictionaries containing message details (id, when, topic) for pending messages.
        """
        now = datetime.datetime.now()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, wen, topic FROM scheduled_messages WHERE wen < ? AND sent = 0",
            (now,),
        )
        # Fetch all pending messages as a list of tuples
        messages = cursor.fetchall()

        # Convert each tuple to a dictionary for easier access
        pending_messages = [
            {"id": message[0], "wen": message[1], "topic": message[2]} for message in messages
        ]
        return pending_messages


# Close the connection when the object is garbage collected
def __del__(self):
    self.conn.close()


# Add the __del__ method to the class
ScheduledMessagesDatabase.__del__ = __del__
