import time
import datetime as dt

GPIO = None


def time_to_datetime(t, datetime_base):
    return datetime_base.replace(hour=t.hour, minute=t.minute,
                                 second=t.second)


class Schedule():
    """Represents open and close events for relay pins."""

    def __init__(self, pins, open_times, close_times):
        self.curr_state = 'off'
        self.pins = pins
        self.open_times = open_times
        self.close_times = close_times

    def get_latest_event(self, now):
        open_event = self._get_latest_event(self.open_times, 'on')
        close_event = self._get_latest_event(self.close_times, 'off')

        if open_event > close_event:
            return open_event
        return close_event

    def _get_latest_event(self, times, status):
        now = dt.datetime.now()
        first_time_today = time_to_datetime(times[0], now)

        if now < first_time_today:
            yesterday = now + dt.timedelta(days=-1)
            yesterday_t = time_to_datetime(times[-1], yesterday)
            return (yesterday_t, status)
        else:
            for schedule_t in times:
                today_t = time_to_datetime(schedule_t, now)
                if now > today_t:
                    return (today_t, status)

    def get_next_event(self, now):
        open_event = self._get_next_event(self.open_times, 'on')
        close_event = self._get_next_event(self.close_times, 'off')

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

        if schedule.curr_state != wanted_state:
            set_relay(schedule.pins, wanted_state)
            schedule.curr_state = wanted_state

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

if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        light_pins = [23, 24]  # GPIO pins of the lights (BCM)
        light_schedule = Schedule(light_pins,
                                  [dt.time(5, 0, 0)], [dt.time(23, 55, 0)])
        fan_schedule = Schedule([22],  # GPIO pins of the fans (BCM)
                                each(3, start_at=dt.time(5, 30, 0),
                                max_iterations=6),
                                each(3, start_at=dt.time(6, 0, 0),
                                max_iterations=6))

        control_relays([light_schedule, fan_schedule])
    except KeyboardInterrupt:
        print('Got KeyboardInterrupt.')
    except Exception as e:
        print('Got unexpected fatal Exception: %s' % str(e))
    finally:
        # Reset GPIO
        GPIO.cleanup()
