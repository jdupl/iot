from sqlalchemy import Column, Integer, String

from database import db_session, Base


# class Record(Base):
#     __tablename__ = 'records'
#     query = db_session.query_property()
#
#     id = Column(Integer, primary_key=True)
#     timestamp = Column(Integer)
#     sensor_uuid = Column(String)
#     value = Column(Integer)
#
#     def __init__(self, sensor_uuid, value, timestamp=None):
#         self.timestamp = timestamp
#         self.value = 1024 - int(value)
#         self.sensor_uuid = sensor_uuid
#
#     def as_pub_dict(self):
#         return {
#             'timestamp': self.timestamp,
#             'sensor_uuid': self.sensor_uuid,
#             'value': self.value
#         }


class HygroRecord(Base):
    __tablename__ = 'records_hygro'
    query = db_session.query_property()

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    sensor_uuid = Column(String)
    value = Column(Integer)

    def __init__(self, sensor_uuid, timestamp, raw_value):
        self.sensor_uuid = sensor_uuid
        self.timestamp = timestamp
        self.value = 1024 - int(raw_value)

    def as_pub_dict(self):
        return {
            'timestamp': self.timestamp,
            'sensor_uuid': self.sensor_uuid,
            'value': self.value
        }


class PhotocellRecord(Base):
    __tablename__ = 'records_photocell'
    query = db_session.query_property()

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    sensor_uuid = Column(String)
    value = Column(Integer)

    def __init__(self, sensor_uuid, timestamp, value):
        self.sensor_uuid = sensor_uuid
        self.timestamp = timestamp
        self.value = int(value)

    def as_pub_dict(self):
        return {
            'timestamp': self.timestamp,
            'sensor_uuid': self.sensor_uuid,
            'value': self.value
        }


class DHT11Record(Base):
    __tablename__ = 'records_dht11'
    query = db_session.query_property()

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    sensor_uuid = Column(String)
    rel_humidity = Column(Integer)
    temperature = Column(Integer)

    def __init__(self, sensor_uuid, timestamp, temperature, rel_humidity):
        self.sensor_uuid = sensor_uuid
        self.timestamp = timestamp
        self.temperature = temperature
        self.rel_humidity = rel_humidity

    def as_pub_dict(self):
        return {
            'timestamp': self.timestamp,
            'sensor_uuid': self.sensor_uuid,
            'rel_humidity': self.rel_humidity,
            'temperature': self.temperature
        }


def dict_to_obj(sensor_type_str, sensor_id, timestamp, args):
    resolver = {
        'hygro': HygroRecord,
        'dht11': DHT11Record,
        'photocell': PhotocellRecord
    }
    if sensor_type_str not in resolver:
        raise Exception('Unknown sensor type')
    return resolver[sensor_type_str](sensor_id, timestamp, *args)
