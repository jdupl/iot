from collectors import collector
from dht11 import DHT11Collector


def collect_data(sensors):
    pass


def get_collectors():
    bcm_pin = 1
    collector_instance = DHT11Collector(bcm_pin)
    return (bcm_pin, read_fn)


if __name__ == '__main__':
    collect_data(get_collectors())
