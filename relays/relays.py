import time
import datetime as dt

GPIO = None


class Schedule():
    """Represents open and close events for relay pins."""

    def __init__(self, pins, open_times, close_times):
        self.__curr_state = 'off'
        self.pins = pins
        self.open_times = open_times
        self.close_times = close_times

    def get_latest_event(self, now=dt.datetime.now()):
        past = sorted(self._get_past_events(now), reverse=True)
        return past[0]

    def get_next_event(self, now=dt.datetime.now()):
        future = sorted(self._get_future_events(now))
        return future[0]

    def _get_future_events(self, now):
        return self._get_events(True, now)

    def _get_past_events(self, now):
        return self._get_events(False, now)

    def _get_events(self, future, now):
        delta = 1 if future else -1

        events = self._build_events(future, delta, 'on', self.open_times, now)
        events += self._build_events(future, delta, 'off',
                                     self.close_times, now)
        return events

    def _build_events(self, future, delta, status, time_array, now):
        events = []

        for i, t in enumerate(time_array):
            event_time = now.replace(hour=t.hour, minute=t.minute,
                                     second=t.second)
            event = (event_time, status)

            if (future and event_time > now) or \
               (not future and event_time < now):
                events.append(event)

            events.append((event_time + dt.timedelta(days=delta), event[1]))
        return events


def get_events(time_array, future):
    events = []
    now = dt.datetime.now()
    delta = 1 if future else -1

    for i, t in enumerate(time_array):
        event_time = now.replace(hour=t.hour, minute=t.minute,
                                 second=t.second)
        event = (event_time, 'on' if i == 0 else 'off')

        if (future and event_time > now) or (not future and event_time < now):
            events.append(event)

        events.append((event_time + dt.timedelta(days=delta), event[1]))
    return events


def get_latest_event(time_array):
    past = sorted(get_events(time_array, False), reverse=True)
    return past[0]


def get_next_event(time_array):
    future = sorted(get_events(time_array, True))
    return future[0]


def set_relay(pins, state_str):
    # Yes, relay on needs gpio value 0
    for pin in pins:
        gpio_val = 1 if state_str == 'off' else 0

        for pin in pins:
            print('Pin %d is now %s (%d)' % (pin, state_str, gpio_val))
            GPIO.output(pin, gpio_val)


def setup_light_pins(pins):
    for pin in pins:
        # Lights are off
        GPIO.setup(pin, GPIO.OUT, initial=1)


def control_and_sleep(schedules):
    now = dt.datetime.now()
    next_event_max = 10
    print('Currently %s.' % str(now))

    for schedule in schedules:
        wanted_state = schedule.get_latest_event()[1]

        if schedule.__curr_state != wanted_state:
            set_relay(schedule.pins, wanted_state)
            schedule.__curr_state = wanted_state

        next_event = schedule.get_next_event()[0]

        if next_event > next_event_max:
            next_event_max = next_event

    next_change_in = (next_event_max - now).total_seconds()
    print('Next_change_in %s' % next_change_in)
    time.sleep(next_change_in)


def control_relays(schedules):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    setup_light_pins(light_pins)

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
