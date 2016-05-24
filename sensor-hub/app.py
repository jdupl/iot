import sys

from flask import Flask, request
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

from database import db_session, init_db, init_engine

app = Flask(__name__)

Base = declarative_base()


class Record(Base):
    __tablename__ = 'records'
    query = db_session.query_property()

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    value = Column(Integer)

    def __init__(self, timestamp, value):
        self.timestamp = timestamp
        self.value = value


@app.route('/', methods=['POST'])
def hub():
    try:
        for r in request.data.decode('utf-8').split('\n'):
            db_session.add(Record(*r.split(',')))
            db_session.commit()

        return 'ok', 200
    except Exception:
        return 'not good', 400


def setup(env=None):
    app.config.from_pyfile('config/default.py')
    app.config.from_pyfile('config/%s.py' % env, silent=True)

    init_engine(app.config['DATABASE_URI'])
    init_db(Base)

    if env == 'test':
        return

    app.run(app.config.get('HOST'))


if __name__ == '__main__':
    setup(sys.argv[1] if len(sys.argv) > 1 else None)
