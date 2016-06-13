# Plant watcher

Collects data from sensors and sends measurements with NTP timestamp to an external server.


## Usage

Connect sensors to analog pins and modifiy collector.ino to your pins (Wi-Fi and sensors) and SSID information.

### Builder
To generate an ino file, compile and upload to arduino from a YAML configuration:

Edit `config/default.py`

`pip3 install -r requirements.txt`

`python3 builder.py`

See `Uploading to an Arduino without IDE` for more information


## LED status

Two leds can be pluged-in to view status. Change RED_LED_PIN and GREEN_LED_PIN to your hardware configuration.

* No LED: Trying to setup Wi-Fi
* Red only: Wi-Fi OK
* Red and green: Wi-Fi and NTP OK
* Green only: Wi-Fi, NTP and server link OK


## Uploading to an Arduino without IDE

Change `_build/Makefile` to your needs.

(`make show_boards` for complete list).

`sudo apt-get install arduino-mk`
