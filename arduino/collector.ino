// Code is based from http://rootpower.com/?p=73 and adapted for my usage
#include <SoftwareSerial.h>

SoftwareSerial softSerial(11, 10); // RX, TX

String SSID = "wifi SSID";
String password = "wifi password";
String serverIp = "(HTTP) Server ip or name";


void setup() {
    Serial.begin(9600);
    softSerial.begin(115200);
    delay(1000);

    softSerial.println("AT+CIOBAUD=9600");
    delay(1000);

    softSerial.begin(9600);
    delay(1000);

    execOnESP("AT+CWMODE=1", "OK", 5000);
    execOnESP("AT+CWJAP=\"" + SSID + "\",\"" + password + "\"", "OK" , 15000);
}

void loop() {
    if (!update()) {
        reset();
    }
    delay(3000);
}

bool update() {
    if (!execOnESP("AT+CIPSTART=\"TCP\",\"" + serverIp + "\",80", "OK", 5000))
        return false;

    String request = "GET / HTTP/1.1\r\n";
    int reqLength = request.length() + 2; // add 2 because \r\n will be appended by SoftwareSerial.println().

    if (!execOnESP("AT+CIPSEND=" + String(reqLength) , "OK", 10000))
        return false;

    if (!execOnESP(request, "+IPD" , 15000))
        return false;
}

void reset() {
    execOnESP("AT+RST", "ready", 20000);
    execOnESP("AT+CWMODE=1", "OK", 5000);
    execOnESP("AT+CWJAP=\"" + SSID + "\",\"" + password + "\"", "OK" , 15000);
}

bool execOnESP(String cmd, String expectedRes, unsigned long timeout) {
    unsigned long tExpire = millis() + timeout;
    String response = "";

    softSerial.println(cmd);

    while (millis() < tExpire) {
        char c = softSerial.read();
        if (c >= 0) {
            response += String(c);
            if (response.indexOf(expectedRes) > 0) {
                return true;
            }
        }
    }

    return false;
}
