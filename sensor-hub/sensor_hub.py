#!/usr/bin/env python3
import sys
import atexit
import threading
import requests

from flask import Flask, request, jsonify
from sqlalchemy import desc, func

# Own modules
import analytics

from database import db_session, init_db
from models import HygroRecord, DHT11Record

POOL_TIME = 5  # Seconds
relays = []
relays_updater = threading.Thread()

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
        HygroRecord.query.group_by(HygroRecord.sensor_uuid)
        .having(func.max(HygroRecord.timestamp)).all())

    for r in records:
        last_watering_timestamp = analytics\
            ._get_last_watering_timestamp(r['sensor_uuid'])

        if last_watering_timestamp:
            polyn = analytics._get_polynomial(
                r['sensor_uuid'], last_watering_timestamp)

            next_watering_timestamp = analytics\
                ._predict_next_watering(polyn, last_watering_timestamp)

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
    records = HygroRecord.query.filter(
        HygroRecord.timestamp >= since_epoch_sec).all()

    for r in records:
        if r.sensor_uuid not in history:
            history[r.sensor_uuid] = []

        history[r.sensor_uuid].append({'x': r.timestamp, 'y': r.value})

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


def _get_relays():
    global relays
    return relays


@app.route('/api/relays', methods=['GET'])
def get_relays():
    return jsonify({'relays': _get_relays()}), 200


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


def extract_object_from_arduino_piece(piece, ):
    piece_dict = (piece).split(':')
    sensor_local_id = piece_dict[0]
    sensor_uuid = "%s_%s" % (arduino_uuid, sensor_local_id)
    sensor_type = sensor_local_id.split('_')[0]
    print(sensor_type)
    print(sensor_uuid)


@app.route('/api/records', methods=['POST'])
def add_record():
    try:
        for timestamp_line in request.data.decode('utf-8').split('\n'):
            pieces = timestamp_line.split(',')
            if len(pieces) < 2:
                return __bad_request()

            timestamp = pieces[0]
            arduino_uuid = pieces[1]  # TODO: Add to DB

            for piece in pieces[2:]:
                obj = extract_object_from_arduino_piece(piece, timestamp,
                                                        arduino_uuid)
                if obj:
                    db_session.add(obj)

                # if key == 'dht11_temp':
                #     temperature = val
                # elif key == 'dht11_humidity':
                #     rel_humidity = val
                # else:
                #     db_session.add(
                #         HygroRecord(*piece_dict, timestamp=timestamp))

            # if temperature and rel_humidity:
            #     dht11_r = DHT11Record(int(temperature), int(rel_humidity),
            #                           timestamp=timestamp)
            #     db_session.add(dht11_r)

        db_session.commit()
        return 'ok', 200
    except Exception:
        return __bad_request()


def _get_new_relays(relays_ip):
    r = requests.get('http://%s/api/relays' % relays_ip)

    if r.status_code == 200:
        return r.json()
    else:
        print(r.status_code)


def interrupt():
    global relays_updater
    relays_updater.cancel()


def setup(env=None):
    def interrupt():
        global relays_updater
        relays_updater.cancel()

    def update_relays():
        global relays
        global relays_updater

        try:
            new_relays = []
            if env != 'test':
                new_relays = _get_new_relays('localhost:8080')
                relays = new_relays
        except Exception as e:
            print(e)

        # Setup next execution
        relays_updater = threading.Timer(POOL_TIME, update_relays, ())
        relays_updater.start()

    def do_update_relays():
        global relays_updater
        relays_updater = threading.Timer(POOL_TIME, update_relays, ())
        relays_updater.start()

    app.config.from_pyfile('config/default.py')
    app.config.from_pyfile('config/%s.py' % env, silent=True)

    init_db(app.config['DATABASE_URI'])

    do_update_relays()
    atexit.register(interrupt)

    return app

if __name__ == '__main__':
    setup(sys.argv[1] if len(sys.argv) > 1 else None).run(use_reloader=False)
