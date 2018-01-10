import datetime as dt
import requests
from time import sleep

from server.database import db_session

from server.util import time_to_datetime


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


def start():
    try:
        print('Starting scheduler process')
        while True:
            call_api()
            sleep(5)
    except KeyboardInterrupt:
        print('Got KeyboardInterrupt.')
    except Exception as e:
        print('Got unexpected fatal Exception: %s' % str(e))
        import traceback
        traceback.print_exc()


def update_pins_on_auto(pins, state_str, GPIO):
    for pin in pins:
        if pin.on_user_override:
            print('Pin %d is on user_override. Keeping current state.'
                  % pin.pin_id)
            GPIO.apply_state(pin.pin_id, pin.state_str)
        else:
            GPIO.apply_state(pin.pin_id, state_str)
            pin.state_str = state_str
            db_session.add(pin)


def call_api():
    r = requests.get('http://127.0.0.1:5002/api/routine')
