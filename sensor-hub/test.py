import os
import json
import unittest
import datetime as dt
import sensor_hub
import csv

from sqlalchemy import desc
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
        self.now = mock_datetime(2016, 7, 18, 16, 25)
        app = sensor_hub.setup('test')
        self.app = app.test_client()

    def tearDown(self):
        db_session.close()
        os.remove('/tmp/test.db')

    def gen_data(self, offset=None):
        self.all_records = []
        with open('fixtures/dht11_data_short.csv') as csvfile:
            reader = csv.reader(csvfile)

            for i, row in enumerate(reader):
                record = Record(row[1], 1024 - int(row[2]), row[0])
                self.all_records.append(record)

                if not offset or i >= offset:
                    db_session.add(record)

            db_session.commit()
            db_session.close()

    def test_get_last_watering_timestamp(self):
        with self.now:
            self.gen_data()
            self.assertEqual(len(self.all_records), 31)
            actual = sensor_hub._get_last_watering_timestamp(1)
            self.assertEqual(1468810074, actual)

    def test_predictions(self):
        with self.now:
            self.gen_data(offset=10)

            records = Record.query.filter(Record.pin_num == 1) \
                .order_by(desc(Record.timestamp)).all()
            self.assertEqual(21, len(records))
            poly = sensor_hub._get_polynomial(1, 1468810074)

            for r in self.all_records[:-2]:
                prediction = sensor_hub._predict_at(
                    float(r.timestamp), poly, 1468810074)
                # err = prediction - float(r.value)
                # print(prediction, r.value, err)

                # Test prediction is ~20% accurate
                self.assertFalse(prediction > float(r.value) * 1.2)
                self.assertFalse(prediction < float(r.value) * 0.8)

            self.assertEqual(sensor_hub._predict_next_watering(
                poly, 1468810074), 1468810074 + 108000)


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
