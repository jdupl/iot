# manage.py
import sys
import atexit

from time import sleep
from multiprocessing import Process
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from server.gpio import OPiGPIOWrapper, RPiGPIOWrapper, GPIOPrintWrapper
from server.models import Pin, Schedule


global child_processes, GPIO


platform_resolver = {
    'computer': GPIOPrintWrapper,
    'opi': OPiGPIOWrapper,
    'rpi': RPiGPIOWrapper
}


def interrupt():
    global child_processes
    for p in child_processes:
        p.terminate()


def start_scheduler(gpio_wrapper, db, Schedule, Pin):
    from server import scheduler
    scheduler.start(gpio_wrapper, db, Schedule, Pin)


def launch_api(app):
    app.run(use_reloader=False, port=app.config['PORT'],
            host=app.config['HOST'])


if __name__ == '__main__':
    global child_processes, GPIO
    child_processes = []

    env = sys.argv[1] if len(sys.argv) > 1 else 'default'
    platform = sys.argv[2] if len(sys.argv) > 2 else 'computer'

    atexit.register(interrupt)
    # Get the GPIO wrapper for the platform
    GPIO = platform_resolver[platform]

    app = Flask(__name__)

    app.config.from_pyfile('server/config/api/default.py')
    app.config.from_pyfile('server/config/api/%s.py' % env, silent=True)
    db = SQLAlchemy(app)

    from server.views import relays_blueprint, static_blueprint

    app.register_blueprint(relays_blueprint)
    app.register_blueprint(static_blueprint)

    # Setup Flask process
    relay_api_process = Process(target=launch_api, args=(app,))
    child_processes.append(relay_api_process)
    relay_api_process.start()
    sleep(0.5)

    # Setup scheduler process
    relays_updater_process = Process(
        target=start_scheduler,
        args=(GPIO, db, Schedule, Pin))
    child_processes.append(relays_updater_process)

    relays_updater_process.start()
    # Let schedule run once
    sleep(0.5)

    if env != 'test':
        relays_updater_process.join()
