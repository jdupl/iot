# manage.py
import sys

from flask import Flask

from server.database import db_session, init_db
from server.models import Pin, Schedule


def create_data():
    env = sys.argv[1] if len(sys.argv) > 1 else 'default'
    print(env)

    app = Flask(__name__)

    app.config.from_pyfile('server/config/api/default.py')
    app.config.from_pyfile('server/config/api/%s.py' % env, silent=True)

    init_db(app.config['DATABASE_URI'])

    lights = Schedule(open_time_sec=5*60*60, run_for_sec=16*60*60)
    db_session.add(lights)

    fans = Schedule(open_time_sec=5*60*60, run_for_sec=5*60, repeat_every=60*60)
    db_session.add(fans)

    db_session.flush()

    p = Pin(pin_id=37, name='L1.1')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=35, name='L1.2')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=33, name='L1.3')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=31, name='L1.4')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=13, name='L1.5')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=16, name='L2.1')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=26, name='L2.2')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=29, name='L2.3')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=18, name='L2.4')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=12, name='L2.5')
    p.schedule_id = lights.id
    db_session.add(p)

    p = Pin(pin_id=36, name='Ventilation')
    p.schedule_id = fans.id
    db_session.add(p)
    db_session.flush()


if __name__ == '__main__':
    create_data()
