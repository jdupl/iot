from sqlalchemy import Column, Integer

from database import db_session, Base


class Record(Base):
    __tablename__ = 'records'
    query = db_session.query_property()

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    pin_num = Column(Integer)
    value = Column(Integer)

    def __init__(self, pin_num, value, timestamp=None):
        self.timestamp = timestamp
        self.value = 1024 - int(value)
        self.pin_num = pin_num

    def as_pub_dict(self):
        return {
            'timestamp': self.timestamp,
            'pin_num': self.pin_num,
            'value': self.value
        }


class DHT11Record(Base):
    __tablename__ = 'records_dht11'
    query = db_session.query_property()

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    rel_humidity = Column(Integer)
    temperature = Column(Integer)

    def __init__(self, temperature, rel_humidity, timestamp=None):
        self.timestamp = timestamp
        self.rel_humidity = rel_humidity
        self.temperature = temperature

    def as_pub_dict(self):
        return {
            'timestamp': self.timestamp,
            'rel_humidity': self.rel_humidity,
            'temperature': self.temperature
        }
