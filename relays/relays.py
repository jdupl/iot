import sys
import yaml
import atexit

from time import sleep
from multiprocessing import Process
from multiprocessing.managers import SyncManager

import relays_api
import scheduler
from scheduler import Schedule

child_processes = []
flask_app = None


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

    def set_user_override(self, state_str):
        self.on_user_override = True
        self.apply_state(state_str)

    def reset_user_override(self):
        # TODO trigger control relay routine
        self.on_user_override = False

    def as_pub_dict(self):
        return {
            'bcm_pin_num': self.bcm_pin_num,
            'state_str': self.state_str,
            'on_user_override': self.on_user_override
        }


def read_config(config_path):
    with open(config_path, 'r') as f:
        yaml_cfg = yaml.load(f.read())
    s = []
    pins = {}

    for node in yaml_cfg:
        repeat_every = None
        start_at = [int(i) for i in node['start_at'].split(':')]
        run_for = [int(i) for i in node['run_for'].split(':')]

        if 'repeat_every' in node:
            repeat_every = [int(i) for i in node['repeat_every'].split(':')]
        s_pins = []
        for p_num in node['gpio_bcm_pins']:
            pins[p_num] = Pin(p_num)
            s_pins.append(p_num)
        s.append(
            Schedule(s_pins, start_at, run_for, repeat_every))
    return s, pins


def interrupt():
    global child_processes, manager
    manager.shutdown()
    for p in child_processes:
        p.terminate()


def start_scheduler(synced_schedules, synced_pins, env):
    scheduler.start(synced_schedules, synced_pins, env)


def launch_api(flask_app):
    flask_app.run(use_reloader=False, port=5002)


def main(env=None, relay_config_path='config/default.yaml'):
    global child_processes, flask_app, manager, GPIO
    atexit.register(interrupt)

    GPIO = FakeGPIO
    if env != 'dev' and env != 'test':
        import RPi.GPIO as _GPIO
        GPIO = _GPIO

    # Setup schedules and pins
    schedules, pins = read_config(relay_config_path)

    # Setup var manager
    manager = SyncManager(address=('127.0.0.1', 5001))
    manager.start()
    manager.connect()
    synced_schedules = manager.list()
    synced_pins = manager.dict()

    for s in schedules:
        synced_schedules.append(s)
    for k, v in pins.items():
        synced_pins[k] = v

    # Setup scheduler process
    relays_updater_process = Process(target=start_scheduler,
                                     args=(synced_schedules, synced_pins,
                                           GPIO,))
    child_processes.append(relays_updater_process)
    relays_updater_process.start()
    # Let schedule run once
    sleep(0.5)

    # Setup Flask process
    flask_app = relays_api.setup(env, synced_schedules, synced_pins)
    relay_api_process = Process(target=launch_api,
                                args=(flask_app,))
    child_processes.append(relay_api_process)
    relay_api_process.start()

    if env != 'test':
        relays_updater_process.join()


if __name__ == '__main__':
    env = sys.argv[1] if len(sys.argv) > 1 else 'default'
    config_path = 'config/%s.yaml' % env
    main(env, config_path)
