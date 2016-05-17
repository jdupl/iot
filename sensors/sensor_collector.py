import time
import csv
import os

from collectors.dht11 import DHT11Collector


def get_sensors():
    c1 = DHT11Collector(14, 'sensor_1.csv')
    c2 = DHT11Collector(15, 'sensor_2.csv')

    return [c1, c2]


def collect_data():
    collector_instances = get_sensors()

    write_csv_headers(collector_instances)

    while True:
        for c in collector_instances:
            r = c.get_data()
            if r:
                write(r, c.csv_path, c)
        time.sleep(60)


def write(result, csv_path, collector_instance):
    with open(csv_path, 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([time.time(), *result])


def write_csv_headers(collector_instances):
    for c in collector_instances:
        csv_path = c.csv_path

        if os.path.exists(csv_path):
            continue

        headers = ['Unix epoch (s)', *c.get_csv_headers()]
        with open(csv_path, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

if __name__ == '__main__':
    collect_data()
