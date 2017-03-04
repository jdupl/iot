import sys
import yaml
import atexit

from time import sleep
from multiprocessing import Process
from multiprocessing.managers import SyncManager

import relays_api
import scheduler
from scheduler import Schedule
from gpio import Pin, OPiGPIOWrapper, RPiGPIOWrapper, GPIOPrintWrapper

child_processes = []
flask_app = None

platform_resolver = {
    'computer': GPIOPrintWrapper,
    'opi': OPiGPIOWrapper,
    'rpi': RPiGPIOWrapper
}


def read_config(config_path, gpio_wrapper):
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
        for p_num in node['pin_ids']:
            pins[p_num] = Pin(p_num, gpio_wrapper)
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
    flask_app.run(use_reloader=False, port=flask_app.config['PORT'],
                  host=flask_app.config['HOST'])


def main(env, platform, relay_config_path='config/default.yaml'):
    global child_processes, flask_app, manager, GPIO
    atexit.register(interrupt)

    # Get the GPIO wrapper for the platform
    GPIO = platform_resolver[platform]

    # Read schedules and pins from config
    schedules, pins = read_config(relay_config_path, GPIO)

    for pin in pins.values():
        pin.setup()

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
    relays_updater_process = Process(
        target=start_scheduler,
        args=(synced_schedules, synced_pins, GPIO,))

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
    platform = sys.argv[2] if len(sys.argv) > 2 else 'computer'
    config_path = 'config/%s.yaml' % env
    main(env, platform, config_path)
