from sqlalchemy import Column, Integer, String, Float

from database import db_session, Base


class Record(object):
    query = db_session.query_property()

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    sensor_uuid = Column(String)

    def __init__(self, sensor_uuid, timestamp, value=None):
        self.sensor_uuid = sensor_uuid
        self.timestamp = timestamp
        if value:
            self.value = int(value)

    def as_pub_dict(self):
        pub = {
            'timestamp': self.timestamp,
            'sensor_uuid': self.sensor_uuid,
        }
        if hasattr(self, 'value'):
            pub['value'] = self.value
        return pub


class HygroRecord(Base, Record):
    __tablename__ = 'records_hygro'

    value = Column(Integer)

    def __init__(self, *args):
        Record.__init__(self, *args)
        self.value = 1024 - int(self.value)


class PhotocellRecord(Base, Record):
    __tablename__ = 'records_photocell'

    value = Column(Integer)

    def __init__(self, *args):
        Record.__init__(self, *args)


class DHT11Record(Base, Record):
    __tablename__ = 'records_dht11'

    rel_humidity = Column(Integer)
    temperature = Column(Integer)

    def __init__(self, sensor_uuid, timestamp, temperature, rel_humidity):
        Record.__init__(self, sensor_uuid, timestamp)
        self.temperature = temperature
        self.rel_humidity = rel_humidity

    def as_pub_dict(self):
        pub = Record.as_pub_dict(self)
        pub['rel_humidity'] = self.rel_humidity
        pub['temperature'] = self.temperature
        return pub


class RainRecord(Base, Record):
    __tablename__ = 'records_rain'

    value = Column(Integer)

    def __init__(self, *args):
        Record.__init__(self, *args)


class BMPRecord(Base, Record):
    __tablename__ = 'records_bmp'

    temperature = Column(Float)
    pressure = Column(Integer)

    def __init__(self, sensor_uuid, timestamp, temperature, pressure):
        Record.__init__(self, sensor_uuid, timestamp)
        self.temperature = int(temperature) / 100.0
        self.pressure = int(pressure)


def dict_to_obj(sensor_type_str, sensor_id, timestamp, args):
    resolver = {
        'hygro': HygroRecord,
        'dht11': DHT11Record,
        'photocell': PhotocellRecord,
        'rain': RainRecord,
        'bmp': BMPRecord
    }
    if sensor_type_str not in resolver:
        raise Exception('Unknown sensor type')
    return resolver[sensor_type_str](sensor_id, timestamp, *args)
