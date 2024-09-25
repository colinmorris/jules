import datetime

TIMESTAMP_FORMATSTRING = "%m/%d/%y %H:%M:%S"

class MalformedDateException(Exception):
    pass

def fmt_timestamp(timestamp):
    """Format timestamp to a string, for example:
        "09/22/24 14:50:05"
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    timestr = dt.strftime(TIMESTAMP_FORMATSTRING)
    return timestr

def parse_timestring(timestring):
    try:
        return datetime.datetime.strptime(timestring, TIMESTAMP_FORMATSTRING)
    except ValueError:
        raise MalformedDateException()

def fmt_now():
    return fmt_timestamp(datetime.datetime.now().timestamp())

