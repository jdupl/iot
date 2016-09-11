import datetime as dt
import unittest

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


class ScheduleTest(unittest.TestCase):

    def test_get_times_of_events_from_simple_schedule(self):
        # No repeat
        s = Schedule(14, (5, 0, 0), (1, 0, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 0)])

        s = Schedule(14, (5, 0, 0), (0, 30, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(5, 30, 0)])

        s = Schedule(14, (5, 0, 0), (0, 0, 1))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(5, 0, 1)])

        # Tests second overflow
        s = Schedule(14, (5, 3, 55), (3, 34, 10))
        self.assertEqual(s.open_events, [dt.time(5, 3, 55)])
        self.assertEqual(s.close_events, [dt.time(8, 38, 5)])

    def test_get_times_of_events_from_repeating_schedule(self):
        s = Schedule(14, (5, 0, 0), (1, 0, 0), (8, 0, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 0, 0),
                                         dt.time(21, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 0), dt.time(14, 0, 0),
                                          dt.time(22, 0, 0)])

        s = Schedule(14, (5, 0, 0), (1, 0, 1), (8, 13, 4))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 13, 4),
                                         dt.time(21, 26, 8)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 1), dt.time(14, 13, 5),
                                          dt.time(22, 26, 9)])

    def test_get_times_of_events_from_repeating_schedule_with_limits(self):
        s = Schedule(14, (5, 0, 0), (1, 0, 0), (8, 0, 0), (21, 0, 0))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 0, 0)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 0), dt.time(14, 0, 0)])

        s = Schedule(14, (5, 0, 0), (1, 0, 1), (8, 13, 4), (21, 26, 9))
        self.assertEqual(s.open_events, [dt.time(5, 0, 0), dt.time(13, 13, 4),
                                         dt.time(21, 26, 8)])
        self.assertEqual(s.close_events, [dt.time(6, 0, 1), dt.time(14, 13, 5),
                                          dt.time(22, 26, 9)])

    # def test_get_events_from_each(self):
    #     start_times = relays.each(1, start_at=dt.time(4, 0, 0))
    #     close_times = relays.each(1, start_at=dt.time(4, 30, 0))
    #     s = Schedule([22], start_times, close_times)
    #
    #     with mock_datetime(2016, 5, 30, 3, 58):
    #         self.assertEqual(s.get_next_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 4, 0), 'on'))
    #
    #         self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 29, 23, 30), 'off'))
    #
    #     with mock_datetime(2016, 5, 30, 4, 1):
    #         self.assertEqual(s.get_next_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 4, 30), 'off'))
    #
    #         self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 4, 0), 'on'))
    #
    #     with mock_datetime(2016, 5, 30, 4, 59):
    #         self.assertEqual(s.get_next_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 5, 0), 'on')
    #                          )
    #
    #         self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 4, 30), 'off'))
    #
    #     with mock_datetime(2016, 5, 30, 6, 1):
    #         self.assertEqual(s.get_next_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 6, 30), 'off')
    #                          )
    #
    #         self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 6, 0), 'on'))
    #
    #     with mock_datetime(2016, 5, 30, 16, 50):
    #         self.assertEqual(s.get_next_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 17, 0), 'on')
    #                          )
    #
    #         self.assertEqual(s.get_latest_event(now=dt.datetime.now()),
    #                          (dt.datetime(2016, 5, 30, 16, 30), 'off'))


if __name__ == '__main__':
    unittest.main()
