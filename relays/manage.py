# manage.py
import sys
import atexit
from time import sleep
from multiprocessing import Process


from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from server.gpio import OPiGPIOWrapper, RPiGPIOWrapper, GPIOPrintWrapper
from server import app, db, launch_api
from server.models import Pin, Schedule


global child_processes, GPIO
child_processes = []
migrate = Migrate(app, db)
manager = Manager(app)

platform_resolver = {
    'computer': GPIOPrintWrapper,
    'opi': OPiGPIOWrapper,
    'rpi': RPiGPIOWrapper
}

# migrations
manager.add_command('db', MigrateCommand)


@manager.command
def create_db():
    """Creates the db tables."""
    db.create_all()


@manager.command
def drop_db():
    """Drops the db tables."""
    db.session.drop_all()


@manager.command
def create_data():
    s = Schedule(open_time_sec=5*60*60, run_for_sec=60*60)
    db.session.add(s)
    db.session.commit()
    p = Pin(pin_id=1)
    p.schedule_id = s.id
    db.session.add(p)
    db.session.commit()


@manager.command
def run_server():
    global child_processes, GPIO
    child_processes = []
    env = sys.argv[1] if len(sys.argv) > 1 else 'default'
    platform = sys.argv[2] if len(sys.argv) > 2 else 'computer'
    atexit.register(interrupt)

    # Get the GPIO wrapper for the platform
    GPIO = platform_resolver[platform]

    # Setup Flask process
    relay_api_process = Process(target=launch_api)
    child_processes.append(relay_api_process)
    relay_api_process.start()
    sleep(0.5)

    # Setup scheduler process
    relays_updater_process = Process(
        target=start_scheduler,
        args=(GPIO, Schedule, Pin))
    child_processes.append(relays_updater_process)

    relays_updater_process.start()
    # Let schedule run once
    sleep(0.5)

    if env != 'test':
        relays_updater_process.join()


def interrupt():
    global child_processes
    for p in child_processes:
        p.terminate()


def start_scheduler(gpio_wrapper, Schedule, Pin):
    from server import scheduler
    scheduler.start(gpio_wrapper, db, Schedule, Pin)


if __name__ == '__main__':
    manager.run()
