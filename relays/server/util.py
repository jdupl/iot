import datetime as dt


def time_to_datetime(t, datetime_base):
    return datetime_base.replace(hour=t.hour, minute=t.minute,
                                 second=t.second)


def time_lt_other(time, other):
    if time.hour > other.hour:
        return False
    if time.hour < other.hour:
        return True

    # Hour is equal
    if time.minute > other.minute:
        return False
    if time.minute < other.minute:
        return True

    # Minute is equal
    if time.second < other.second:
        return True
    return False


def add_delta_to_rel_time(t, delta):
    return (dt.datetime.combine(dt.date.today(), t) + delta).time()


def tuple_to_timedelta(t):
    return dt.timedelta(hours=t[0], minutes=t[1], seconds=t[2])
