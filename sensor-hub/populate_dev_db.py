#!/usr/bin/env python3
import os
import csv

from sensor_hub import db_session, Record, setup


def setUp():
    os.remove('/tmp/dev.db')
    setup('dev')
    db_session.close()


def create_records():
    with open('fixtures/dht11_data.csv') as csvfile:
        reader = csv.reader(csvfile)

        for i, row in enumerate(reader):
            record = Record(row[1], 1024 - int(row[2]), row[0])
            db_session.add(record)

        db_session.commit()
        db_session.close()

if __name__ == '__main__':
    setup()
    create_records()
