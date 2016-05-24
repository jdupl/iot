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
        record = Record(1464191598, 1024)
        db_session.add(record)
        db_session.commit()
        records = Record.query.all()
        assert len(records) == 1
        self.assertEqual(records[0].timestamp, 1464191598)
        self.assertEqual(records[0].value, 1024)

    def test_single_message(self):
        res = self.app.post('/', data='1464191598,1024')
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 1
        self.assertEqual(records[0].timestamp, 1464191598)
        self.assertEqual(records[0].value, 1024)

    def test_multiple_message(self):
        data = ("1464181598,1024\n"
                "1464191598,1024")
        res = self.app.post('/', data=data)
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 2

    def test_not_good(self):
        data = ("1024")
        res = self.app.post('/', data=data)
        assert res.status_code == 400
        records = Record.query.all()
        assert len(records) == 0

if __name__ == '__main__':
    unittest.main()
