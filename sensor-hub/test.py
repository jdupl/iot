import os
from app import app, db, Record
import unittest
import tempfile

class HelloWorld(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.db = db
        self.db.session.close()
        self.db.drop_all()
        self.db.create_all()

    def test_hello_world(self):
        res = self.app.get('/')
        data = res.data.decode('utf-8')
        assert data == 'Hello World!'

    def test_create_record(self):
        record = Record(1024)
        self.db.session.add(record)
        self.db.session.commit()
        records = Record.query.all()
        assert len(records) == 1

    def test_single_message(self):
        res = self.app.post('/', data='1024')
        assert res.status_code == 200
        records = Record.query.all()
        assert len(records) == 1

if __name__ == '__main__':
    unittest.main()
