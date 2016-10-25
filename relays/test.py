import unittest
import json
import datetime as dt

from unittest.mock import MagicMock

import relays
from relays import Schedule, Pin, app


class mock_datetime(object):
    """
    Monkey-patch datetime for predictable results.
    From https://github.com/dbader/schedule/blob/master/test_schedule.py
    """
    def __init__(self, year, month, day, hour, minute):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute

    def __enter__(self):
        class MockDate(dt.datetime):
            @classmethod
            def today(cls):
                return cls(self.year, self.month, self.day)

            @classmethod
            def now(cls):
                return cls(self.year, self.month, self.day,
                           self.hour, self.minute)
        self.original_datetime = dt.datetime
        dt.datetime = MockDate

    def __exit__(self, *args, **kwargs):
        dt.datetime = self.original_datetime


class ConfigTest(unittest.TestCase):

    def test_get_schedule_from_config(self):
        actuals = relays.read_config('fixtures/test_config_simple.yaml')

        expected = Schedule([Pin(14)], (5, 0, 0), (1, 0, 0))
        actual = actuals[0]

        self.assertEqual(expected.pins, actual.pins)
        self.assertEqual(expected.open_events, actual.open_events)
        self.assertEqual(expected.close_events, actual.close_events)

        expected = Schedule([Pin(23), Pin(12)], (8, 0, 0), (12, 0, 0))
        actual = actuals[1]

        self.assertEqual(expected.pins, actual.pins)
        self.assertEqual(expected.open_events, actual.open_events)
        self.assertEqual(expected.close_events, actual.close_events)

    def test_get_schedule_from_config_repeating(self):
        actuals = relays.read_config('fixtures/test_config_repeating.yaml')

        expected = Schedule([Pin(14), Pin(76)],
                            (5, 0, 0), (0, 5, 0), (1, 0, 0))
        actual = actuals[0]
        self.assertEqual(expected.pins, actual.pins)
        self.assertEqual(expected.open_events, actual.open_events)
        self.assertEqual(expected.close_events, actual.close_events)

        expected = Schedule([Pin(23), Pin(12)],
                            (8, 0, 0), (0, 0, 30), (0, 30, 0))
        actual = actuals[1]

        self.assertEqual(expected.pins, actual.pins)
        self.assertEqual(expected.open_events, actual.open_events)
        self.assertEqual(expected.close_events, actual.close_events)


class ScheduleTest(unittest.TestCase):

    def test_get_times_of_events_from_simple_schedule(self):
        # No repeat
        s = Schedule(Pin(14), (5, 0, 0), (1, 0, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 0)])

        s = Schedule(Pin(14), (5, 0, 0), (0, 30, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(5, 30, 0)])

        s = Schedule(Pin(14), (5, 0, 0), (0, 0, 1))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(5, 0, 1)])

        # Tests second overflow
        s = Schedule(Pin(14), (5, 3, 55), (3, 34, 10))
        self.assertEqual(s.open_events, [dt.time(5, 3, 55)])
        self.assertEqual(s.close_events, [dt.time(8, 38, 5)])

    def test_get_times_of_events_from_repeating_schedule(self):
        s = Schedule(Pin(14), (5, 0, 0), (1, 0, 0), (8, 0, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 0, 0),
                                         dt.time(21, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 0), dt.time(14, 0, 0),
                                          dt.time(22, 0, 0)])

        s = Schedule(Pin(14), (5, 0, 0), (1, 0, 1), (8, 13, 4))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 13, 4),
                                         dt.time(21, 26, 8)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 1), dt.time(14, 13, 5),
                                          dt.time(22, 26, 9)])

    def test_get_times_of_events_from_repeating_schedule_with_limits(self):
        s = Schedule(Pin(14), (5, 0, 0), (1, 0, 0), (8, 0, 0), (21, 0, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 0), dt.time(14, 0, 0)])

        s = Schedule(Pin(14), (5, 0, 0), (1, 0, 1), (8, 13, 4), (21, 26, 9))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 13, 4),
                                         dt.time(21, 26, 8)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 1), dt.time(14, 13, 5),
                                          dt.time(22, 26, 9)])

    def test_get_events_from_simple_schedule(self):
        with mock_datetime(2016, 5, 1, 5, 1):
            # No repeat, opens at 5:00 closes at 6:00
            s = Schedule(Pin(14), (5, 0, 0), (1, 0, 0))

            self.assertEqual(
                s.get_latest_event(now=dt.datetime.now()),
                (dt.datetime(2016, 5, 1, 5, 0), 'on'))

            self.assertEqual(
                s.get_next_event(now=dt.datetime.now()),
                (dt.datetime(2016, 5, 1, 6, 0), 'off'))

    def test_get_events_from_repeating_schedule_with_limits(self):
        # TODO
        pass

    def test_get_events_from_repeating_schedule(self):
        s = Schedule(Pin(14), (4, 0, 0), (0, 30, 0), (1, 0, 0))

        with mock_datetime(2016, 5, 30, 3, 58):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 4, 0), 'on'))
            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 29, 23, 30), 'off'))

        with mock_datetime(2016, 5, 30, 4, 1):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 4, 30), 'off'))

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 4, 0), 'on'))

        with mock_datetime(2016, 5, 30, 4, 59):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 5, 0), 'on'))

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 4, 30), 'off'))

        with mock_datetime(2016, 5, 30, 6, 1):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 6, 30), 'off'))

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 6, 0), 'on'))

        with mock_datetime(2016, 5, 30, 16, 50):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 17, 0), 'on'))

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 16, 30), 'off'))


class PinTest(unittest.TestCase):

    def test_pins_on_auto_have_their_state_updated(self):
        gpio = MagicMock()
        gpio.output = MagicMock()
        relays.GPIO = gpio

        pin1 = Pin(14)
        pin2 = Pin(15)
        relays.update_pins_on_auto([pin1, pin2], 'on')

        assert gpio.output.call_count == 2
        assert pin1.state_str == 'on'
        assert pin2.state_str == 'on'

    def test_pins_on_override_dont_have_their_state_updated(self):
        gpio = MagicMock()
        gpio.output = MagicMock()
        relays.GPIO = gpio

        pin1 = Pin(14)
        pin1.on_user_override = True
        pin2 = Pin(15)

        relays.update_pins_on_auto([pin1, pin2], 'on')
        assert gpio.output.call_count == 1
        assert pin1.state_str == 'off'
        assert pin2.state_str == 'on'


class RelayApiTest(unittest.TestCase):

    def setUp(self):
        relays.setup('test', 'config/test.yaml')
        self.app = app.test_client()

    def tearDown(self):
        relays.interrupt()

    def test_relay_api_send_relays(self):
        res = self.app.get('/api/relays')
        assert res.status_code == 200

        relays = json.loads(res.data.decode('utf8'))
        assert 'relays' in relays
        relays = relays['relays']

        assert len(relays) == 1
        assert relays[0]['state_str'] == 'on'

if __name__ == '__main__':
    unittest.main()
