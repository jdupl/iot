import time
import datetime as dt


open_time = dt.time(5, 0, 0)
close_time = dt.time(23, 55, 0)
light_pins = [23, 24]  # GPIO pins of the relay (BCM)

GPIO = None


class Schedule():
    """Represents open and close events for relay pins."""
    def __init__(self, pins, open_times, close_times):
        self.pins = pins
        self.open_times = open_times
        self.close_times = close_times

    def get_future_events(self, now=dt.datetime.now()):
        return self._get_events(True, now)

    def get_past_events(self, now=dt.datetime.now()):
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


def load_config():
    return True


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


def lights(state_str):
    # Yes, relay on needs gpio value 0
    gpio_val = 1 if state_str == 'off' else 0

    for pin in light_pins:
        print('Pin %d is now %s (%d)' % (pin, state_str, gpio_val))
        GPIO.output(pin, gpio_val)


def setup_light_pins(pins):
    for pin in pins:
        # Lights are off
        GPIO.setup(pin, GPIO.OUT, initial=1)


def control_lights():
    __curr_state = 'off'
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    setup_light_pins(light_pins)

    while True:
        now = dt.datetime.now()
        print('Currently %s.' % str(now))

        wanted_state = get_latest_event([open_time, close_time])[1]

        if __curr_state != wanted_state:
            print('Bringing lights %s.' % wanted_state)
            lights(wanted_state)
            __curr_state = wanted_state

        next_event = get_next_event([open_time, close_time])[0]
        next_change_in = (next_event - now).total_seconds()
        print('Next_change_in %s' % next_change_in)

        sleep_until = next_change_in + 1
        time.sleep(sleep_until)

if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        control_lights()
    except KeyboardInterrupt:
        print('Got KeyboardInterrupt.')
    except Exception as e:
        print('Got unexpected fatal Exception: %s' % str(e))
    finally:
        # Reset GPIO
        GPIO.cleanup()
