# manage.py
import sys
import atexit

from time import sleep
from multiprocessing import Process
from flask import Flask
from server.database import init_db

from server import scheduler
from server.gpio import OPiGPIOWrapper, RPiGPIOWrapper, GPIOPrintWrapper


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


def start_scheduler():
    scheduler.start()


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

    app.config['GPIO'] = GPIO()

    init_db(app.config['DATABASE_URI'])

    from server.views import relays_blueprint, static_blueprint

    app.register_blueprint(relays_blueprint)
    app.register_blueprint(static_blueprint)

    # Setup Flask process
    relay_api_process = Process(target=launch_api, args=(app,))
    child_processes.append(relay_api_process)
    relay_api_process.start()
    sleep(0.5)

    # Setup scheduler process
    relays_updater_process = Process(target=start_scheduler)
    child_processes.append(relays_updater_process)
    relays_updater_process.start()

    if env != 'test':
        relays_updater_process.join()
