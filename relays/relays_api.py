from flask import Flask, jsonify, request

app = Flask(__name__)


def launch_api(relay_api_app):
    relay_api_app.run(use_reloader=False)


def __to_pub_list(elements):
    return list(map(lambda e: e.as_pub_dict(), elements))


@app.route('/api/relays', methods=['GET'])
def get_relays():
    global synced_pins
    pins = []
    for p in synced_pins.values():
        pins.append(p)

    return jsonify({'relays': __to_pub_list(pins)}), 200


@app.route('/api/relays/<pin_id>', methods=['POST'])
def put_relays(pin_id):
    data = request.form
    p = synced_pins[int(pin_id)]

    wanted_state = data['state_str']
    reset_to_auto = wanted_state == 'auto'

    if reset_to_auto:
        p.reset_user_override()
    else:
        p.set_user_override(wanted_state)

    # Share to other processes
    synced_pins[pin_id] = p

    return jsonify({'relay': synced_pins[pin_id].as_pub_dict()}), 200


def setup(env, _synced_schedules, _synced_pins):
    global synced_pins, synced_schedules
    synced_pins = _synced_pins
    synced_schedules = _synced_schedules

    app.config.from_pyfile('config/api/default.py')
    app.config.from_pyfile('config/api/%s.py' % env, silent=True)

    return app
