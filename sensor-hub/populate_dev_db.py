#!/usr/bin/env python3
import os
import csv

from datetime import datetime as dt
from sensor_hub import setup
from database import db_session
from models import Record, DHT11Record


def setUp():
    os.remove('/tmp/dev.db')
    setup('dev')
    db_session.close()


def create_records(pin_num):
    with open('fixtures/rel_humidity_data.csv') as csvfile:
        reader = csv.reader(csvfile)
        f = reader.__next__()
        delay = dt.now().timestamp() - int(f[0])

        record = Record(pin_num, int(f[2]), int(f[0]) + delay)
        db_session.add(record)

        for row in reader:
            record = Record(pin_num, int(row[2]), int(row[0]) + delay)
            db_session.add(record)

        db_session.commit()
        db_session.close()

    with open('fixtures/dht11_data.csv') as csvfile:
        reader = csv.reader(csvfile)
        f = reader.__next__()
        delay = dt.now().timestamp() - int(f[0])

        record = DHT11Record(int(f[1]), int(f[2]), int(f[0]) + delay)
        db_session.add(record)

        for row in reader:
            r = DHT11Record(int(row[1]), int(row[2]), int(row[0]) + delay)
            db_session.add(r)

        db_session.commit()
        db_session.close()


if __name__ == '__main__':
    setup()
    create_records(1)
    create_records(7)
