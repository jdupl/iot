import datetime as dt
from time import sleep
#
# from relays import db
from server.database import db_session

from server.util import time_to_datetime

GPIO = None
Pin = None
Schedule = None


def get_next_event(schedule, now):
    if not hasattr(schedule, 'open_events'):
        schedule.create_events()
    open_event = _get_next_event(schedule, schedule.open_events, 'on')
    close_event = _get_next_event(schedule, schedule.close_events, 'off')

    if open_event < close_event:
        return open_event
    return close_event


def _get_next_event(schedule, times, status):
    now = dt.datetime.now()
    last_time_today = time_to_datetime(times[-1], now)

    if now < last_time_today:
        for schedule_t in times:
            today_t = time_to_datetime(schedule_t, now)

            if now < today_t:
                return (today_t, status)
    else:
        tommorow = now + dt.timedelta(days=1)
        tommorow_t = time_to_datetime(times[0], tommorow)
        return (tommorow_t, status)


def get_latest_event(schedule, now):
    if not hasattr(schedule, 'open_events'):
        schedule.create_events()
    open_event = _get_latest_event(schedule, schedule.open_events, 'on')
    close_event = _get_latest_event(schedule, schedule.close_events, 'off')

    if open_event > close_event:
        return open_event
    return close_event


def _get_latest_event(schedule, times, status):
    times_reverse = times[:]
    times_reverse.reverse()

    now = dt.datetime.now()
    first_time_today = time_to_datetime(times[0], now)

    if now < first_time_today:
        yesterday = now + dt.timedelta(days=-1)
        yesterday_t = time_to_datetime(times[-1], yesterday)
        return (yesterday_t, status)
    else:
        for schedule_t in times_reverse:
            today_t = time_to_datetime(schedule_t, now)
            if now > today_t:
                return (today_t, status)


def start(_GPIO, _Schedule, _Pin):
    global GPIO, Schedule, Pin
    GPIO = _GPIO()
    Schedule = _Schedule
    Pin = _Pin

    try:
        print('Starting scheduler process')
        control_relays()
    except KeyboardInterrupt:
        print('Got KeyboardInterrupt.')
    except Exception as e:
        print('Got unexpected fatal Exception: %s' % str(e))
        import traceback
        traceback.print_exc()
    finally:
        # Reset GPIO
        GPIO.cleanup()


def control_relays():
    while True:
        schedules = Schedule.query.all()

        pins_dict = {}
        for pin in Pin.query.all():
            pins_dict[pin.pin_id] = pin

        control_and_sleep(schedules, pins_dict)
        # sleep(1)  # Overflow next schedule


def update_pins_on_auto(pins, state_str, pins_dict):
    for pin in pins:
        if pin.on_user_override:
            print('Pin %d is on user_override. Keeping current state.'
                  % pin.pin_id)
        else:
            GPIO.apply_state(pin.pin_id, state_str)
            pin.state_str = state_str
            db_session.add(pin)


def control_and_sleep(schedules, synced_pins):
    now = dt.datetime.now()
    print('Currently %s.' % str(now))

    for schedule in schedules:
        wanted_state = get_latest_event(schedule, now)[1]
        update_pins_on_auto(schedule.pins, wanted_state, synced_pins)

    next_change_in = get_sleep_for(schedules, dt.datetime.now())
    print('Next_change_in %s' % next_change_in)

    sleep(next_change_in)


def get_sleep_for(schedules, now):
    next_event = None

    for schedule in schedules:
        schedule_next_event = get_next_event(schedule, now)[0]
        if not next_event or schedule_next_event < next_event:
            next_event = schedule_next_event

    return (next_event - now).total_seconds()
