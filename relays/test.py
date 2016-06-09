import datetime as dt
import unittest

import relays
from relays import Schedule


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


class UtilsTest(unittest.TestCase):

    def test_each(self):
        times = relays.each(3, start_at=dt.time(3, 59, 0))
        self.assertEqual(times, [dt.time(3, 59, 0), dt.time(6, 59, 0),
                                 dt.time(9, 59, 0), dt.time(12, 59, 0),
                                 dt.time(15, 59, 0), dt.time(18, 59, 0),
                                 dt.time(21, 59, 0)])


class ScheduleTest(unittest.TestCase):

    def test_get_latest_event_from_simple_schedule(self):
        s = Schedule(14, [dt.time(5, 0, 0)], [dt.time(15, 0, 0)])

        with mock_datetime(2016, 5, 30, 3, 58):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 5, 0), 'on'))

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 29, 15, 0), 'off'))

        with mock_datetime(2016, 5, 30, 14, 0):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 15, 0), 'off'))

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 5, 0), 'on'))

        with mock_datetime(2016, 5, 30, 16, 0):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 31, 5, 0), 'on'))

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 15, 0), 'off'))

    def test_get_events_from_each(self):
        start_times = relays.each(1, start_at=dt.time(4, 0, 0))
        close_times = relays.each(1, start_at=dt.time(4, 30, 0))
        s = Schedule([22], start_times, close_times)

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
                             (dt.datetime(2016, 5, 30, 5, 0), 'on')
                             )

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 4, 30), 'off'))

        with mock_datetime(2016, 5, 30, 6, 1):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 6, 30), 'off')
                             )

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 6, 0), 'on'))

        with mock_datetime(2016, 5, 30, 16, 50):
            self.assertEqual(s.get_next_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 17, 0), 'on')
                             )

            self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
                             (dt.datetime(2016, 5, 30, 16, 30), 'off'))


if __name__ == '__main__':
    unittest.main()
