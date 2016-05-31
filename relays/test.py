import datetime as dt
import unittest

from relays import Schedule


class RelayTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_events_from_simple_schedule_morning(self):
        # It's 4h
        now = dt.datetime.fromtimestamp(1464595200)
        open_time = dt.time(5, 0, 0)
        close_time = dt.time(23, 55, 0)
        s = Schedule(14, [open_time], [close_time])

        self.assertEqual(len(s.get_future_events(now=now)), 4)
        self.assertEqual(s.get_future_events(now=now), [
            (dt.datetime(2016, 5, 30, 5, 0), 'on'),
            (dt.datetime(2016, 5, 31, 5, 0), 'on'),
            (dt.datetime(2016, 5, 30, 23, 55), 'off'),
            (dt.datetime(2016, 5, 31, 23, 55), 'off'),
        ])

        self.assertEqual(len(s.get_past_events(now=now)), 2)
        self.assertEqual(s.get_past_events(now=now), [
            (dt.datetime(2016, 5, 29, 5, 0), 'on'),
            (dt.datetime(2016, 5, 29, 23, 55), 'off'),
        ])

    def test_get_events_from_simple_schedule_noon(self):
        # It's about 23h
        now = dt.datetime.fromtimestamp(1464663600)
        open_time = dt.time(5, 0, 0)
        close_time = dt.time(23, 55, 0)
        s = Schedule(14, [open_time], [close_time])

        self.assertEqual(len(s.get_future_events(now=now)), 3)
        self.assertEqual(s.get_future_events(now=now), [
            (dt.datetime(2016, 5, 31, 5, 0), 'on'),
            (dt.datetime(2016, 5, 30, 23, 55), 'off'),
            (dt.datetime(2016, 5, 31, 23, 55), 'off'),
        ])
        self.assertEqual(len(s.get_past_events(now=now)), 3)
        self.assertEqual(s.get_past_events(now=now), [
            (dt.datetime(2016, 5, 30, 5, 0), 'on'),
            (dt.datetime(2016, 5, 29, 5, 0), 'on'),
            (dt.datetime(2016, 5, 29, 23, 55), 'off'),
        ])

    def test_get_events_from_simple_schedule_evening(self):
        # It's 23h56
        now = dt.datetime.fromtimestamp(1464666960)
        open_time = dt.time(5, 0, 0)
        close_time = dt.time(23, 0, 0)
        s = Schedule(14, [open_time], [close_time])

        self.assertEqual(len(s.get_future_events(now=now)), 2)
        self.assertEqual(s.get_future_events(now=now), [
            (dt.datetime(2016, 5, 31, 5, 0), 'on'),
            (dt.datetime(2016, 5, 31, 23, 0), 'off'),
        ])
        self.assertEqual(len(s.get_past_events(now=now)), 4)
        self.assertEqual(s.get_past_events(now=now), [
            (dt.datetime(2016, 5, 30, 5, 0), 'on'),
            (dt.datetime(2016, 5, 29, 5, 0), 'on'),
            (dt.datetime(2016, 5, 30, 23, 0), 'off'),
            (dt.datetime(2016, 5, 29, 23, 0), 'off'),
        ])

    def test_get_events_from_multiple_schedule(self):
        # It's 4h
        now = dt.datetime.fromtimestamp(1464595200)
        s = Schedule(14, [dt.time(5, 0, 0), dt.time(15, 0, 0)],
                     [dt.time(10, 0, 0), dt.time(19, 0, 0)])

        self.assertEqual(len(s.get_future_events(now=now)), 8)
        self.assertEqual(s.get_future_events(now=now), [
            (dt.datetime(2016, 5, 30, 5, 0), 'on'),
            (dt.datetime(2016, 5, 31, 5, 0), 'on'),
            (dt.datetime(2016, 5, 30, 15, 0), 'on'),
            (dt.datetime(2016, 5, 31, 15, 0), 'on'),
            (dt.datetime(2016, 5, 30, 10, 0), 'off'),
            (dt.datetime(2016, 5, 31, 10, 0), 'off'),
            (dt.datetime(2016, 5, 30, 19, 0), 'off'),
            (dt.datetime(2016, 5, 31, 19, 0), 'off'),
        ])

        self.assertEqual(len(s.get_past_events(now=now)), 4)
        self.assertEqual(s.get_past_events(now=now), [
            (dt.datetime(2016, 5, 29, 5, 0), 'on'),
            (dt.datetime(2016, 5, 29, 15, 0), 'on'),
            (dt.datetime(2016, 5, 29, 10, 0), 'off'),
            (dt.datetime(2016, 5, 29, 19, 0), 'off'),
        ])

if __name__ == '__main__':
    unittest.main()
