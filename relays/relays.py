import time
import yaml
import datetime as dt

GPIO = None


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


class Schedule():
    """Represents daily events schedule for relays."""

    def __init__(self, pins, open_time, run_for, repeat_every=None,
                 repeat_until=None):
        """
        pins: GPIO BCM pins to control
        open_time: First open time of the day
        run_for: Keep open for this amount of time (tuple of (h, m, s))
        repeat_every: Repeat each amount of time (tuple of (h, m, s)) or 'None'
                      if event shouldn't be repeated more than once a day.
                      Starts at the open time so this parameter must be
                      longer than 'run_for'.
        repeat_until: Repeat schedule until (tuple of (h, m, s)) or 'None' if
                      it should be repeated until the day ends.
        """
        self.pins = pins
        self.first_open = dt.time(*open_time)
        run_for = tuple_to_timedelta(run_for)
        t = self.first_open

        # Lists containing events relative times
        self.open_events = []
        self.close_events = []

        if repeat_every:
            repeat_every = tuple_to_timedelta(repeat_every)
        else:
            self.open_events.append(t)
            self.close_events.append(add_delta_to_rel_time(t, run_for))
            return

        if not repeat_until:
            # Set max cut off if not provided
            repeat_until = dt.time(23, 59, 59)
        else:
            repeat_until = dt.time(*repeat_until)

        while True:
            last = t
            o_time = t
            c_time = add_delta_to_rel_time(t, run_for)

            self.open_events.append(o_time)
            self.close_events.append(c_time)

            t = add_delta_to_rel_time(t, repeat_every)

            if not time_lt_other(t, repeat_until) or time_lt_other(t, last):
                break

    def get_latest_event(self, now):
        open_event = self._get_latest_event(self.open_events, 'on')
        close_event = self._get_latest_event(self.close_events, 'off')

        if open_event > close_event:
            return open_event
        return close_event

    def _get_latest_event(self, times, status):
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

    def get_next_event(self, now):
        open_event = self._get_next_event(self.open_events, 'on')
        close_event = self._get_next_event(self.close_events, 'off')

        if open_event < close_event:
            return open_event
        return close_event

    def _get_next_event(self, times, status):
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


def set_relay(pins, state_str):
    # Yes, relay on needs gpio value 0
    for pin in pins:
        gpio_val = 1 if state_str == 'off' else 0

        for pin in pins:
            print('Pin %d is now %s (%d)' % (pin, state_str, gpio_val))
            GPIO.output(pin, gpio_val)


def setup_pins(pins):
    for pin in pins:
        # Off
        GPIO.setup(pin, GPIO.OUT, initial=1)


def control_and_sleep(schedules):
    now = dt.datetime.now()
    print('Currently %s.' % str(now))

    for schedule in schedules:
        wanted_state = schedule.get_latest_event(now)[1]
        set_relay(schedule.pins, wanted_state)

    next_change_in = get_sleep_for(schedules, dt.datetime.now())

    print('Next_change_in %s' % next_change_in)
    time.sleep(next_change_in)


def get_sleep_for(schedules, now):
    next_event = None

    for schedule in schedules:
        schedule_next_event = schedule.get_next_event(now)[0]
        if not next_event or schedule_next_event < next_event:
            next_event = schedule_next_event

    return (next_event - now).total_seconds()


def control_relays(schedules):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    for schedule in schedules:
        setup_pins(schedule.pins)

    while True:
        control_and_sleep(schedules)
        time.sleep(1)  # Overflow next schedule


def each(hours, start_at=dt.time(0, 0, 0), max_iterations=24):
    times = []
    time = start_at
    t_hour = time.hour

    while t_hour < 24 and \
            (max_iterations > 0 and max_iterations > len(times)):
        t = dt.time(t_hour, time.minute, time.second)
        times.append(t)
        t_hour = time.hour + (hours) * (len(times))

    return times


def read_config(config_path='config/default.yaml'):
    with open(config_path, 'r') as f:
        yaml_cfg = yaml.load(f.read())
    s = []

    for node in yaml_cfg:
        repeat_every = None
        start_at = [int(i) for i in node['start_at'].split(':')]
        run_for = [int(i) for i in node['run_for'].split(':')]

        if 'repeat_every' in node:
            repeat_every = [int(i) for i in node['repeat_every'].split(':')]

        s.append(
            Schedule(node['gpio_bcm_pins'], start_at, run_for, repeat_every))
    return s

if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        control_relays(read_config())

    except KeyboardInterrupt:
        print('Got KeyboardInterrupt.')
    except Exception as e:
        print('Got unexpected fatal Exception: %s' % str(e))
    finally:
        # Reset GPIO
        GPIO.cleanup()
