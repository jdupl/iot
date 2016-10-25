import sys
import time
import yaml
import atexit
import datetime as dt

from multiprocessing import Process, Queue
from schedule import Schedule
from flask import Flask, jsonify


class FakeGPIO():

    BCM = 'bcm'
    OUT = 'out'

    def setwarnings(*args, **kwargs):
        pass

    def setmode(*args, **kwargs):
        pass

    def setup(*args, **kwargs):
        pass

    def output(*args, **kwargs):
        pass

    def cleanup(*args, **kwargs):
        pass


GPIO = FakeGPIO
relays_updater = None

app = Flask(__name__)
q = Queue(20)
schedules_cache = []


class Pin():
    def __init__(self, bcm_pin_num, user_override=False):
        self.bcm_pin_num = bcm_pin_num
        self.state_str = 'off'
        self.on_user_override = user_override

    def __eq__(self, o):
        return self.bcm_pin_num == o.bcm_pin_num and \
            self.state_str == o.state_str

    def apply_state(self, state_str):
        # 'on' is 0 on normally closed relay
        gpio_val = 1 if state_str == 'off' else 0
        try:
            GPIO.output(self.bcm_pin_num, gpio_val)

            self.state_str = state_str
            print('Pin %d is now %s (%d)' % (self.bcm_pin_num,
                                             state_str, gpio_val))
        except Exception as e:
            print('Problem while changing pin %d status: '
                  % self.bcm_pin_num, e)

    def as_pub_dict(self):
        return {
            'bcm_pin_num': self.bcm_pin_num,
            'state_str': self.state_str,
            'on_user_override': self.on_user_override
        }


def update_pins_on_auto(pins, state_str):
    for pin in pins:
        if pin.on_user_override:
            print('Pin %d is on user_override. Keeping current state.'
                  % pin.bcm_pin_num)
        else:
            pin.apply_state(state_str)


def setup_pins(pins):
    for pin in pins:
        # Off
        GPIO.setup(pin.bcm_pin_num, GPIO.OUT, initial=1)


def control_and_sleep(schedules, queue):
    now = dt.datetime.now()
    print('Currently %s.' % str(now))

    for schedule in schedules:
        wanted_state = schedule.get_latest_event(now)[1]
        update_pins_on_auto(schedule.pins, wanted_state)

    queue.put(schedules)

    next_change_in = get_sleep_for(schedules, dt.datetime.now())

    print('Next_change_in %s' % next_change_in)
    time.sleep(next_change_in)


def get_sleep_for(schedules, now):
    next_event = None

    for schedule in schedules:
        schedule_next_event = schedule.get_next_event(now)[0]
        if not next_event or schedule_next_event < next_event:
            next_event = schedule_next_event

    return (next_event - now).total_seconds()


def control_relays(schedules, queue):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    for schedule in schedules:
        setup_pins(schedule.pins)

    while True:
        control_and_sleep(schedules, queue)
        time.sleep(1)  # Overflow next schedule


def read_config(config_path):
    with open(config_path, 'r') as f:
        yaml_cfg = yaml.load(f.read())
    s = []

    for node in yaml_cfg:
        repeat_every = None
        start_at = [int(i) for i in node['start_at'].split(':')]
        run_for = [int(i) for i in node['run_for'].split(':')]

        if 'repeat_every' in node:
            repeat_every = [int(i) for i in node['repeat_every'].split(':')]
        s_pins = []
        for p_num in node['gpio_bcm_pins']:
            s_pins.append(Pin(p_num))
        s.append(
            Schedule(s_pins, start_at, run_for, repeat_every))
    return s


def __to_pub_list(elements):
    return list(map(lambda e: e.as_pub_dict(), elements))


@app.route('/api/relays', methods=['GET'])
def get_relays():
    global schedules_cache
    while not q.empty():
        schedules_cache = q.get()
    pins = []
    for s in schedules_cache:
        pins.extend(s.pins)
    return jsonify({'relays': __to_pub_list(pins)}), 200


def interrupt():
    global relays_updater
    if relays_updater:
        relays_updater.terminate()


def setup(env=None, relay_config_path='config/default.yaml'):
    global relays_updater

    def update_relays(schedules, queue):
        if env != 'dev' and env != 'test':
            import RPi.GPIO as GPIO
        else:
            GPIO = FakeGPIO

        try:
            control_relays(schedules, queue)
        except KeyboardInterrupt:
            print('Got KeyboardInterrupt.')
        except Exception as e:
            print('Got unexpected fatal Exception: %s' % str(e))
        finally:
            # Reset GPIO
            GPIO.cleanup()

    app.config.from_pyfile('config/api/default.py')
    app.config.from_pyfile('config/api/%s.py' % env, silent=True)

    schedules = read_config(relay_config_path)
    relays_updater = Process(target=update_relays, args=(schedules, q,))
    relays_updater.start()
    atexit.register(interrupt)

    return app

if __name__ == '__main__':
    setup(sys.argv[1] if len(sys.argv) > 1 else None).run(use_reloader=False)
