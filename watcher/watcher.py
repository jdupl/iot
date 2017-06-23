from time import sleep
import csv
import Adafruit_DHT

sensor = Adafruit_DHT.DHT22

# RPi GPIO 23
pin = 23

# humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
humidity = 54
temperature = 52


def main():
    while True:
        if humidity is not None and temperature is not None:
            print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'
                  .format(temperature, humidity))

            with open('data_watcher.csv', 'a') as csvfile:
                spamwriter = csv.writer(csvfile)
                spamwriter.writerow([temperature] + [humidity])
        else:
            print('Failed to get reading')
        sleep(5)


if __name__ == '__main__':
    main()
