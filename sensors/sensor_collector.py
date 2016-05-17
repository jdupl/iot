import time
import csv
import os

from collectors.dht11 import DHT11Collector


def collect_data():
    collector_instance = DHT11Collector(14)
    csv_path = 'sensor_1.csv'

    write_csv_headers(csv_path, collector_instance)

    while True:
        r = collector_instance.get_data()
        if r:
            write(r, csv_path, collector_instance)
        time.sleep(60)


def write(result, csv_path, collector_instance):
    with open(csv_path, 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([time.time(), *result])


def write_csv_headers(csv_path, collector_instance):
    if os.path.exists(csv_path):
        return
    with open(csv_path, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Unix epoch (s)',
                        *collector_instance.get_csv_headers()])

if __name__ == '__main__':
    collect_data()
