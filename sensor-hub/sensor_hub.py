#!/usr/bin/env python3

# External modules
import sys

from flask import Flask, request, jsonify
from sqlalchemy import desc, func

# Own modules
import analytics

from database import db_session, init_db
from models import Record, DHT11Record

app = Flask(__name__)


def __bad_request():
    return 'not good', 400


def __to_pub_list(elements):
    return list(map(lambda e: e.as_pub_dict(), elements))


def get_latest_soil_humidity():
    """Gets latest info about soil humdity and predict waterings.
    """

    pub = []
    records = __to_pub_list(
        Record.query.group_by(Record.pin_num)
        .having(func.max(Record.timestamp)).all())

    for r in records:
        last_watering_timestamp = analytics\
            ._get_last_watering_timestamp(r['pin_num'])

        if last_watering_timestamp:
            polyn = analytics._get_polynomial(
                r['pin_num'], last_watering_timestamp)

            next_watering_timestamp = analytics._predict_next_watering(
                    polyn, last_watering_timestamp)

            r['last_watering_timestamp'] = last_watering_timestamp
            r['next_watering_timestamp'] = next_watering_timestamp
        pub.append(r)

    return pub


def get_lastest_dht11():
    obj = DHT11Record.query.order_by(desc(DHT11Record.timestamp)).first()
    if obj:
        return obj.as_pub_dict()


def get_soil_humidity_history(since_epoch_sec):
    """Gets history of multiple soil humidity sensor.
    Returns array of histories.
    """

    history = {}
    records = Record.query.filter(Record.timestamp >= since_epoch_sec).all()

    for r in records:
        if r.pin_num not in history:
            history[r.pin_num] = []

        history[r.pin_num].append({'x': r.timestamp, 'y': r.value})

    return history


def get_dht11_history(since_epoch_sec):
    """Gets history from a single DHT11 sensor."""

    history = {
        'temperature': [],
        'rel_humidity': []
    }
    records = DHT11Record.query\
        .filter(DHT11Record.timestamp >= since_epoch_sec).all()

    for r in records:
        history['temperature'].append({'x': r.timestamp, 'y': r.temperature})
        history['rel_humidity'].append({'x': r.timestamp, 'y': r.rel_humidity})

    return history


@app.route('/api/records/latest', methods=['GET'])
def get_lastest_records():

    return jsonify({'latest': {
        'soil_humidity': get_latest_soil_humidity(),
        'dht11': get_lastest_dht11(),
    }}), 200


@app.route('/api/records/<since_epoch_sec>', methods=['GET'])
def get_records_history(since_epoch_sec):

    return jsonify({'history': {
        'soil_humidity': get_soil_humidity_history(since_epoch_sec),
        'dht11': get_dht11_history(since_epoch_sec)
    }}), 200


@app.route('/api/records', methods=['POST'])
def add_record():
    try:
        for timestamp_line in request.data.decode('utf-8').split('\n'):
            pieces = timestamp_line.split(',')
            if len(pieces) < 2:
                return __bad_request()

            timestamp = pieces[0]
            temperature = None
            rel_humidity = None

            for piece in pieces[1:]:
                piece_dict = (piece).split(':')
                key = piece_dict[0]
                val = piece_dict[1]

                if key == 'dht11_temp':
                    temperature = val
                elif key == 'dht11_humidity':
                    rel_humidity = val
                else:
                    db_session.add(Record(*piece_dict, timestamp=timestamp))

            if temperature and rel_humidity:
                dht11_r = DHT11Record(int(temperature), int(rel_humidity),
                                      timestamp=timestamp)
                db_session.add(dht11_r)

        db_session.commit()
        return 'ok', 200
    except Exception:
        return __bad_request()


def setup(env=None):
    app.config.from_pyfile('config/default.py')
    app.config.from_pyfile('config/%s.py' % env, silent=True)

    init_db(app.config['DATABASE_URI'])

    return app

if __name__ == '__main__':
    setup(sys.argv[1] if len(sys.argv) > 1 else None).run()
