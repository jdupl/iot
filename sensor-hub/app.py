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
    value = Column(Integer)

    def __init__(self, value):
        self.value = value


@app.route('/', methods=['POST'])
def hub():
    data = request.data
    records = data.decode('utf-8').split('\n')

    for val in records:
        record = Record(val)
        db_session.add(record)
        db_session.commit()
    return 'ok'


def setup(env=None):
    app.config.from_pyfile('config/default.py')
    app.config.from_pyfile('config/%s.py' % env, silent=True)

    init_engine(app.config['DATABASE_URI'])
    init_db(Base)

    if env == 'test':
        return

    host = None
    if app.config.get('HOST'):
        host = app.config['HOST']

    app.run(host)


if __name__ == '__main__':
    setup(sys.argv[1] if len(sys.argv) > 1 else None)
