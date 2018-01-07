from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, create_session
from sqlalchemy.ext.declarative import declarative_base

engine = None
metadata = MetaData()

db_session = scoped_session(
    lambda: create_session(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db(uri):
    global engine
    engine = create_engine(uri, convert_unicode=True)
    Base.metadata.create_all(bind=engine)
    return engine
