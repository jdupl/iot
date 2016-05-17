import time
import csv

from collectors.dht11 import DHT11Collector


def collect_data():
    collector_instance = DHT11Collector(14)
    csv_path = 'sensor_1.csv'

    while True:
        r = collector_instance.get_data()
        if r:
            write(r, csv_path)
        time.sleep(60)


def write(result, csv_path):
    with open(csv_path, 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([time.time(), *result])

if __name__ == '__main__':
    collect_data()
