#!/usr/bin/env python3
import os
import datetime as dt

from app import db_session, Record, setup


def setUp():
    os.remove('/tmp/dev.db')
    setup('dev')
    db_session.close()


def create_records():
    v = 200
    for h in range(0, 47):
        v += 15
        date = dt.datetime.now() - dt.timedelta(hours=h, minutes=1)
        record = Record(7, v % 1024, int(date.timestamp()))
        db_session.add(record)
    db_session.commit()

if __name__ == '__main__':
    setup()
    create_records()
