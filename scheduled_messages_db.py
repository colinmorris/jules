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
        # NB: id is the tool call id we get back from the model. That is supposed to be
        # unique in the context of a session, but I don't know how strong that guarantee is
        # in general, and in particular I have seen that it definitely is possible for the 
        # model to reuse ids if the corresponding tool invocation isn't sent to them as part
        # of the message history (either because we reset the message history or because it
        # fell out of the context window). 
        # The reason for the model returning a unique id in the first place is so that the 
        # caller can do some bookkeeping when they send back the model the results of the 
        # function call. That's not so important in this use case. So maybe we just use
        # an autoincrementing primary key, and keep the id column (w/o unique constraint)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT,
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

    def mark_message_sent(self, rowid):
        """Mark the "sent" flag to true for message with given rowid.

        Args:
            rowid: rowid of the message to mark as sent
        """
        # Update the sent flag for the specific message
        self.conn.execute(
            "UPDATE scheduled_messages SET sent = 1 WHERE rowid = ?", (rowid,)
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
            {"id": message[0], "when": message[1], "topic": message[2]} for message in messages
        ]
        return pending_messages


# Close the connection when the object is garbage collected
def __del__(self):
    self.conn.close()


# Add the __del__ method to the class
ScheduledMessagesDatabase.__del__ = __del__
