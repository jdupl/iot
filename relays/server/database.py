from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, create_session
from sqlalchemy.ext.declarative import declarative_base

engine = None
metadata = MetaData()

db_session = scoped_session(
    lambda: create_session(autocommit=True, autoflush=True, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_engine(uri):
    global engine
    engine = create_engine(uri, convert_unicode=True)
    return engine


def init_db():
    global engine
    metadata.create_all(bind=engine)
