import os
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
        res = self.app.post('/', data='1464191598,7:1024')
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 1
        self.assertEqual(records[0].timestamp, 1464191598)
        self.assertEqual(records[0].pin_num, 7)
        self.assertEqual(records[0].value, 1024)

    def test_single_message_multiple_sensors(self):
        res = self.app.post('/', data='1464191598,7:1024,8:768')
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
        res = self.app.post('/', data=data)
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 3

    def test_not_good(self):
        data = ('1024')
        res = self.app.post('/', data=data)
        assert res.status_code == 400
        records = Record.query.all()
        assert len(records) == 0

if __name__ == '__main__':
    unittest.main()
