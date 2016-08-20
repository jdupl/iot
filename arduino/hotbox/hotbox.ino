#include <dht11.h>

dht11 DHT11;

int WANTED_TEMP = 26;
int LOW_TEMP = 25;  // Thresold to start warming

int WANTED_HUMIDITY = 60;
int HIGH_HUMIDITY = 70;  // Thresold to start venting
int LOW_HUMIDITY = 30;  // Thresold to warn of low humidity


int DHT11_PIN = 2;
int HEATING_PIN = 3;
int VENTING_PIN = 4;

int MAX_ROUTINE_TIME = 60 * 1000;  // Stop routines after 1 minute

int readDHT11WithRetries(int maxRetries) {
    int tries = 0;

    while (tries++ < maxRetries) {
        int res = DHT11.read(DHT11_PIN);

        switch (res) {
        case DHTLIB_OK:
            return DHTLIB_OK

        case DHTLIB_ERROR_CHECKSUM:
            Serial.println("Checksum error");
            break;

        case DHTLIB_ERROR_TIMEOUT:
            Serial.println("Time out error");
            break;

        default:
            Serial.println("Unknown error");
            break;
        }
        delay(500);
    }
}

void warmup() {
    // Heat until WANTED_TEMP or LOW_HUMIDITY is reached
    reset();
    unsigned long tExpire = millis() + MAX_ROUTINE_TIME;

    digitalWrite(HEATING_PIN, 1);
    digitalWrite(VENTING_PIN, 1);

    while (millis() < tExpire) {
        if (!updateDHT11Data()) {
            return reset();
        }

        if (dht11.temperature >= WANTED_TEMP) {
            return reset();
        }
        if (dht11.humidity <= LOW_HUMIDITY) {
            return reset();
        }
        delay(1000);
    }
}

void ventilate() {
    // Air is too hot or humid. Ventilate until LOW_TEMP or WANTED_HUMIDITY is reached.
    reset();
    unsigned long tExpire = millis() + MAX_ROUTINE_TIME;

    digitalWrite(VENTING_PIN, 1);

    while (millis() < tExpire) {
        if (!updateDHT11Data()) {
            return reset();
        }

        if (dht11.temperature <= LOW_TEMP) {
            return reset();
        }
        if (dht11.humidity <= WANTED_HUMIDITY) {
            return reset();
        }
        delay(1000);
    }
}

void warn() {
    // TODO light up red LED
}

void reset() {
    pinMode(HEATING_PIN, OUTPUT);
    pinMode(VENTING_PIN, OUTPUT);
    digitalWrite(HEATING_PIN, 0);
    digitalWrite(VENTING_PIN, 0);
}

void setup() {
    reset();
}

boolean updateDHT11Data() {
    return readDHT11WithRetries(5) == DHTLIB_OK;
}

void loop() {
    if (updateDHT11Data()) {
        if (dht11.temperature <= LOW_TEMP) {
            warmup();
        } else if (dht11.temperature > WANTED_TEMP || dht11.humidity > HIGH_HUMIDITY) {
            ventilate();
        } else if (dht11.humidity < LOW_HUMIDITY) {
            warn();
        }
    } else {
        warn();
    }
    delay(10 * 1000);
}
