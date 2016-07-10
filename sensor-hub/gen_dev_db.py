#!/usr/bin/env python3
import os
import json
import unittest
import datetime as dt

from app import app, db_session, Record, setup


def setUp():
    os.remove('/tmp/dev.db')
    setup('dev')
    app = app.test_client()
    db_session.close()


def create_records():
    v = 200
    for h in range(0, 47):
        v += 15
        date = dt.datetime.now() - dt.timedelta(hours=h, minutes=1)
        record = Record(7, v % 1024, int(date.timestamp()))
        db_session.add(record)
    db_session.commit()
    records = Record.query.all()

if __name__ == '__main__':
    setup()
    create_records()
