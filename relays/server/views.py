import datetime as dt

from flask import Blueprint, jsonify, request, send_from_directory
from flask import current_app as app

from server.database import db_session
from server.models import Pin, Schedule
from server.scheduler import update_pins_on_auto, get_latest_event

relays_blueprint = Blueprint('relays', __name__,)
static_blueprint = Blueprint('static', __name__,)


def __to_pub_list(elements):
    return list(map(lambda e: e.as_pub_dict(), elements))


@relays_blueprint.route('/api/relays', methods=['GET'])
def get_relays():
    return jsonify({'relays': __to_pub_list(Pin.query.all())}), 200


@relays_blueprint.route('/api/routine', methods=['GET'])
def run_relay_routine():
    gpio = app.config['GPIO']
    now = dt.datetime.now()
    print('Currently %s.' % str(now))

    for schedule in Schedule.query.all():
        wanted_state = get_latest_event(schedule, now)[1]
        update_pins_on_auto(schedule.pins, wanted_state, gpio)

    return jsonify({'success': 'ok'}), 200


@relays_blueprint.route('/api/relays/<pin_id>', methods=['POST'])
def put_relays(pin_id):
    data = request.get_json()
    wanted_state = data.get('state_str')
    reset_to_auto = wanted_state == 'auto'

    p = Pin.query.filter(Pin.pin_id == int(pin_id)).one()

    if reset_to_auto:
        p.reset_user_override()
    else:
        p.set_user_override(wanted_state)
    db_session.add(p)
    db_session.flush()

    p = Pin.query.filter(Pin.pin_id == int(pin_id)).one()

    return jsonify({'relay': p.as_pub_dict()}), 200


@static_blueprint.route('/')
def index():
    return send_from_directory('server/public', 'index.html')


@static_blueprint.route('/<path:path>')
def static_files(path):
    return send_from_directory('server/public', path)
