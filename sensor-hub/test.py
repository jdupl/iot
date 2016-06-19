import os
import json
import unittest

from app import app, db_session, Record, setup


class HubTest(unittest.TestCase):

    def setUp(self):
        setup('test')
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


if __name__ == '__main__':
    unittest.main()
