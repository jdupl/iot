import os
import json
import unittest
import datetime as dt
import sensor_hub

from sensor_hub import app, db_session, Record


class HubTest(unittest.TestCase):

    def setUp(self):
        sensor_hub.setup('test')
        self.app = app.test_client()
        db_session.close()

    def tearDown(self):
        os.remove('/tmp/test.db')

    def test_create_record(self):
        record = Record(7, 1024, 1464191598)
        db_session.add(record)
        db_session.commit()
        records = Record.query.all()
        assert len(records) == 1
        self.assertEqual(records[0].timestamp, 1464191598)
        self.assertEqual(records[0].pin_num, 7)
        self.assertEqual(records[0].value, 1024)

    def test_single_message_single_sensor(self):
        res = self.app.post('/api/records', data='1464191598,7:1024')
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 1
        self.assertEqual(records[0].timestamp, 1464191598)
        self.assertEqual(records[0].pin_num, 7)
        self.assertEqual(records[0].value, 1024)

    def test_single_message_multiple_sensors(self):
        res = self.app.post('/api/records', data='1464191598,7:1024,8:768')
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 2
        self.assertEqual(records[0].timestamp, 1464191598)
        self.assertEqual(records[0].pin_num, 7)
        self.assertEqual(records[0].value, 1024)
        self.assertEqual(records[1].timestamp, 1464191598)
        self.assertEqual(records[1].pin_num, 8)
        self.assertEqual(records[1].value, 768)

    def test_multiple_messages(self):
        data = ('1464181598,7:1024\n'
                '1464191598,6:768,9:512')
        res = self.app.post('/api/records', data=data)
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 3

    def test_not_good(self):
        data = ('1024')
        res = self.app.post('/api/records', data=data)
        assert res.status_code == 400
        records = Record.query.all()
        assert len(records) == 0

    def test_get_lastest(self):
        db_session.add(Record(1, 1024, 1464191598))
        db_session.add(Record(2, 1023, 1464191598))
        db_session.add(Record(3, 1022, 1464191598))

        db_session.add(Record(1, 1021, 1564191598))
        db_session.add(Record(2, 1020, 1564191598))

        db_session.add(Record(1, 1, 1364191598))
        db_session.add(Record(2, 2, 1364191598))
        db_session.add(Record(3, 3, 1364191598))

        db_session.commit()

        res = self.app.get('/api/records/latest')
        assert res.status_code == 200
        records = json.loads(res.data.decode('utf8'))
        assert 'records' in records
        records = records['records']
        self.assertEqual(3, len(records))

        self.assertEqual(records[0]['pin_num'], 1)
        self.assertEqual(records[0]['timestamp'], 1564191598)
        self.assertEqual(records[0]['value'], 1021)

        self.assertEqual(records[1]['pin_num'], 2)
        self.assertEqual(records[1]['timestamp'], 1564191598)
        self.assertEqual(records[1]['value'], 1020)

        self.assertEqual(records[2]['pin_num'], 3)
        self.assertEqual(records[2]['timestamp'], 1464191598)
        self.assertEqual(records[2]['value'], 1022)

    def test_get_history(self):
        db_session.add(Record(1, 100, 1468588400))

        db_session.add(Record(1, 1024, 1468939853))
        db_session.add(Record(2, 1023, 1468939853))
        db_session.add(Record(3, 1022, 1468939853))

        db_session.add(Record(1, 1021, 1468853452))
        db_session.add(Record(2, 1020, 1468853452))
        db_session.add(Record(3, 1020, 1468853452))

        db_session.add(Record(1, 1, 1468883452))
        db_session.add(Record(2, 2, 1468883452))
        db_session.add(Record(3, 3, 1468883452))

        db_session.commit()

        res = self.app.get('/api/records/1468688400')
        assert res.status_code == 200
        history = json.loads(res.data.decode('utf8'))
        assert 'history' in history
        history = history['history']
        self.assertEqual(3, len(history))

        self.assertEqual(3, len(history['1']))
        self.assertEqual(history['1'][0]['x'], 1468939853)
        self.assertEqual(history['1'][0]['y'], 1024)
        self.assertEqual(history['1'][1]['x'], 1468853452)
        self.assertEqual(history['1'][1]['y'], 1021)
        self.assertEqual(history['1'][2]['x'], 1468883452)
        self.assertEqual(history['1'][2]['y'], 1)

        self.assertEqual(3, len(history['2']))
        self.assertEqual(history['2'][0]['x'], 1468939853)
        self.assertEqual(history['2'][0]['y'], 1023)
        self.assertEqual(history['2'][1]['x'], 1468853452)
        self.assertEqual(history['2'][1]['y'], 1020)
        self.assertEqual(history['2'][2]['x'], 1468883452)
        self.assertEqual(history['2'][2]['y'], 2)

        self.assertEqual(3, len(history['3']))
        self.assertEqual(history['3'][0]['x'], 1468939853)
        self.assertEqual(history['3'][0]['y'], 1022)
        self.assertEqual(history['3'][1]['x'], 1468853452)
        self.assertEqual(history['3'][1]['y'], 1020)
        self.assertEqual(history['3'][2]['x'], 1468883452)
        self.assertEqual(history['3'][2]['y'], 3)


class AnalyticsTest(unittest.TestCase):

    def setUp(self):
        app = sensor_hub.setup('test')
        self.app = app.test_client()

    def tearDown(self):
        os.remove('/tmp/test.db')

    def test_get_last_watering(self):
        with mock_datetime(2016, 5, 30, 3, 58):
            min_val = 200
            v = 200
            for h in range(0, 65):
                v += 15
                date = dt.datetime.now() - dt.timedelta(hours=h, minutes=1)
                record = Record(7, (v + min_val) % 1024, int(date.timestamp()))
                db_session.add(record)
            db_session.commit()
            db_session.close()

            actual = sensor_hub._get_last_watering(7)
            self.assertEqual(1464447420, actual)


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


if __name__ == '__main__':
    unittest.main()
