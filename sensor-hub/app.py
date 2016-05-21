from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base

from database import db_session, init_db, init_engine

app = Flask(__name__)

Base = declarative_base()


class Record(Base):
    __tablename__ = 'records'

    id = Column(Integer, primary_key=True)
    value = Column(Integer)


# class Record(Base):
#     __tablename__ = 'records'
#
#     id = Column(Integer, primary_key=True)
#     value = Column(String, nullable=False, unique=True)
#

@app.route('/', methods=['POST'])
def hub():
    data = request.data
    records = data.decode('utf-8').split('\n')
    for val in records:
        record = Record(val)
        db.session.add(record)
        db.session.commit()
    return 'ok'


def setup(env):
    app.config.from_pyfile('config/default.py')
    app.config.from_pyfile('config/%s.py' % env, silent=True)

    init_engine(app.config['DATABASE_URI'])
    init_db()
    app.run()


if __name__ == '__main__':
    setup('dev')
