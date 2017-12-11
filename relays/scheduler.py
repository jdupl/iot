import datetime as dt
from time import sleep


GPIO = None


def start(schedules, synced_pins, _GPIO):
    global GPIO
    GPIO = _GPIO()

    try:
        control_relays(schedules, synced_pins)
    except KeyboardInterrupt:
        print('Got KeyboardInterrupt.')
    except Exception as e:
        print('Got unexpected fatal Exception: %s' % str(e))
    finally:
        # Reset GPIO
        GPIO.cleanup()


def control_relays(schedules, synced_pins):
    while True:
        control_and_sleep(schedules, synced_pins)
        sleep(1)  # Overflow next schedule


def update_pins_on_auto(pin_nums, state_str, synced_pins):
    for pin_num in pin_nums:
        pin = synced_pins[pin_num]
        if pin.on_user_override:
            print('Pin %d is on user_override. Keeping current state.'
                  % pin.pin_id)
        else:
            GPIO.apply_state(pin_num, state_str)
        synced_pins[pin_num] = pin


def control_and_sleep(schedules, synced_pins):
    now = dt.datetime.now()
    print('Currently %s.' % str(now))

    for schedule in schedules:
        wanted_state = schedule.get_latest_event(now)[1]
        update_pins_on_auto(schedule.pins, wanted_state, synced_pins)

    next_change_in = get_sleep_for(schedules, dt.datetime.now())
    print('Next_change_in %s' % next_change_in)
    sleep(next_change_in)


def get_sleep_for(schedules, now):
    next_event = None

    for schedule in schedules:
        schedule_next_event = schedule.get_next_event(now)[0]
        if not next_event or schedule_next_event < next_event:
            next_event = schedule_next_event

    return (next_event - now).total_seconds()


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
