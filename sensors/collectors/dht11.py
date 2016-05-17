from .collector import Collector
from dht11 import DHT11


class DHT11Collector(Collector):

    def get_data(self):
        sensor = DHT11(self.pin_num)
        return sensor.get_result()
