#!/usr/bin/env python3
import sys
import requests

from flask import Flask, request, jsonify, send_from_directory
from sqlalchemy import func

# Own modules
import analytics

from database import db_session, init_db
import models
from models import HygroRecord, DHT11Record, PhotocellRecord, BMPRecord, \
    RainRecord

POOL_TIME = 5  # Seconds
relays = []

app = Flask(__name__)


def __bad_request():
    return 'not good', 400


def __forbidden():
    return 'not the good token', 403


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
    return __to_pub_list(
        DHT11Record.query.group_by(DHT11Record.sensor_uuid)
        .having(func.max(DHT11Record.timestamp)).all())


def get_lastest_photocell():
    return __to_pub_list(
        PhotocellRecord.query.group_by(PhotocellRecord.sensor_uuid)
        .having(func.max(PhotocellRecord.timestamp)).all())


def get_lastest_rain():
    return __to_pub_list(
        RainRecord.query.group_by(RainRecord.sensor_uuid)
        .having(func.max(RainRecord.timestamp)).all())


def get_lastest_bmp():
    return __to_pub_list(
        BMPRecord.query.group_by(BMPRecord.sensor_uuid)
        .having(func.max(BMPRecord.timestamp)).all())


def get_soil_humidity_history(since_epoch_sec):
    """Gets history of multiple soil humidity sensors.
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


def get_photocell_history(since_epoch_sec):
    """Gets history of multiple photocell sensors.
    Returns array of histories.
    """

    history = {}
    records = PhotocellRecord.query.filter(
        PhotocellRecord.timestamp >= since_epoch_sec).all()

    for r in records:
        if r.sensor_uuid not in history:
            history[r.sensor_uuid] = []

        history[r.sensor_uuid].append({'x': r.timestamp, 'y': r.value})

    return history


def get_dht11_history(since_epoch_sec):
    """Gets history from DHT11 sensors."""

    history = {}
    records = DHT11Record.query\
        .filter(DHT11Record.timestamp >= since_epoch_sec).all()

    for r in records:
        if r.sensor_uuid not in history:
            history[r.sensor_uuid] = []

        history[r.sensor_uuid].append({
            'x': r.timestamp,
            'temperature': r.temperature,
            'rel_humidity': r.rel_humidity
        })
    return history


def get_dht11_history_weather(since_epoch_sec):
    """Gets history from a DHT11 sensors."""

    history = []
    records = DHT11Record.query\
        .filter(DHT11Record.timestamp >= since_epoch_sec).all()

    for r in records:
        history.append({
            'x': r.timestamp,
            'temperature': r.temperature,
            'rel_humidity': r.rel_humidity
        })
    return history


def get_bmp_history_weather(since_epoch_sec):
    """Gets history from BMP sensors."""

    history = []
    records = BMPRecord.query\
        .filter(BMPRecord.timestamp >= since_epoch_sec).all()

    for r in records:
        history.append({
            'x': r.timestamp,
            'temperature': r.temperature,
            'pressure_kpa': round(r.pressure / 1000.0, 2)
        })
    return history


def get_rain_history_weather(since_epoch_sec):
    """Gets history from rain sensors."""

    history = []
    records = RainRecord.query\
        .filter(RainRecord.timestamp >= since_epoch_sec).all()

    for r in records:
        history.append({
            'x': r.timestamp,
            'value': r.value
        })
    return history


@app.route('/api/relays', methods=['GET'])
def get_relays():
    r = requests.get('%s/api/relays' % app.config['RELAYS_HOST'])
    return jsonify(r.json()), 200


@app.route('/api/relays/<id>', methods=['POST'])
def put_relays(id):
    r = requests.post('%s/api/relays/%s' % (app.config['RELAYS_HOST'], id),
                      data=request.json)
    return jsonify(r.json()), 200


@app.route('/api/records/latest', methods=['GET'])
def get_lastest_records():
    if app.config['WEATHER_MODE']:
        return jsonify({'latest': {
            'dht11': get_lastest_dht11(),
            'rain': get_lastest_rain(),
            'bmp': get_lastest_bmp(),
        }}), 200

    return jsonify({'latest': {
        'soil_humidity': get_latest_soil_humidity(),
        'dht11': get_lastest_dht11(),
        'photocell': get_lastest_photocell()
    }}), 200


def get_records_history_weather(since_epoch_sec):
    combined = {
        'dht11': [],
        'bmp': []
    }
    dht11 = get_dht11_history_weather(since_epoch_sec)
    for r in dht11:
        combined['dht11'].append(r)

    bmp = get_bmp_history_weather(since_epoch_sec)
    for r in bmp:
        combined['bmp'].append(r)

    return jsonify({'history': {
        'combined': combined,
        'dht11': get_dht11_history_weather(since_epoch_sec),
        'rain': get_rain_history_weather(since_epoch_sec),
        'bmp': get_bmp_history_weather(since_epoch_sec),
    }}), 200


@app.route('/api/records/<since_epoch_sec>', methods=['GET'])
def get_records_history(since_epoch_sec):
    if app.config['WEATHER_MODE']:
        return get_records_history_weather(since_epoch_sec)

    return jsonify({'history': {
        'soil_humidity': get_soil_humidity_history(since_epoch_sec),
        'dht11': get_dht11_history(since_epoch_sec),
        'photocell': get_photocell_history(since_epoch_sec)
        }}), 200


@app.route('/api/records', methods=['POST'])
def add_record():
    try:
        lines = request.data.decode('utf-8').split('\n')
        secret = lines[0]
        if secret != app.config['IOT_SECRET']:
            return __forbidden()

        del lines[0:1]

        for timestamp_line in lines:
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

        db_session.commit()
        return 'ok', 200
    except Exception as e:
        print(e)
        return __bad_request()


@app.route('/')
def index():
    if not app.config['DEBUG']:
        return __bad_request()

    if app.config['WEATHER_MODE']:
        return send_from_directory('public/weather', 'index.html')
    return send_from_directory('public', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    if not app.config['DEBUG']:
        return __bad_request()

    if '.' not in path:
        return index()

    if app.config['WEATHER_MODE']:
        return send_from_directory('public/weather', path)
    return send_from_directory('public', path)


def extract_object_from_arduino_piece(piece, timestamp, arduino_uuid):
    piece_dict = (piece).split(':')
    sensor_local_id = piece_dict[0]
    sensor_uuid = "%s_%s" % (arduino_uuid, sensor_local_id)

    sensor_type = sensor_local_id.split('_')[0]
    args = piece_dict[1].split(';')

    return models.dict_to_obj(sensor_type, sensor_uuid, timestamp, args)


def setup(env=None):
    app.config.from_pyfile('config/default.py')
    app.config.from_pyfile('config/%s.py' % env, silent=True)

    init_db(app.config['DATABASE_URI'])
    return app


if __name__ == '__main__':
    app = setup(sys.argv[1] if len(sys.argv) > 1 else None)
    app.run(use_reloader=False, port=app.config['PORT'],
            host=app.config['HOST'])
