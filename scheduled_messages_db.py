import datetime

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
        pass

    def add_scheduled_message(self, id, when, topic):
        """Record scheduled message with given params.
        id: tool call id returned by llm, e.g. "call_9pw1qnYScqvGrCH58HWCvFH6"
        when: datetime string, e.g. "09/22/24 14:00:00"
        topic: topic of message, e.g. "Check up on user"
        """
        dt = date_utils.parse_timestring(when)
        if dt < datetime.datetime.now():
            raise TimeTravelException()
        pass

    def mark_message_sent(self, id):
        """Mark the "sent" flag to true for message with given id.
        """
        pass

    def get_pending_messages(self):
        """Return all messages where scheduled time < now and sent is false.
        """
        pass
