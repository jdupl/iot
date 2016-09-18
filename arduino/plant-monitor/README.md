# Plant watcher

Collects data from sensors and sends measurements with NTP timestamp to an external server.


## Usage

Connect sensors to analog pins and modifiy collector.ino to your pins (Wi-Fi and sensors) and SSID information.

### Builder
To generate an ino file, compile and upload to arduino from a YAML configuration:

Edit `config/default.yaml` or create a new one.

`pip3 install -r requirements.txt`

To use default config:

`python3 builder.py`

To use 'config/my_conf.yaml':

`python3 builder.py my_conf`

See `Uploading to an Arduino without IDE` for more information


## LED status

Two leds can be pluged-in to view status. Change RED_LED_PIN and GREEN_LED_PIN to your hardware configuration.

* No LED: Trying to setup Wi-Fi
* Red only: Wi-Fi OK
* Red and green: Wi-Fi and NTP OK
* Green only: Wi-Fi, NTP and server link OK


## Uploading to an Arduino without IDE

Change `_build/Makefile` to your needs.

`make show_boards` for complete list of boards.

Install make depedencies

`sudo apt-get install arduino-mk`
