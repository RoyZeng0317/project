#include <TinyGPS++.h>
#include <SoftwareSerial.h>

#define RX_PIN 4
#define TX_PIN 3

TinyGPSPlus gps;
SoftwareSerial gpsSerial(RX_PIN, TX_PIN);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  gpsSerial.begin(9600);

  Serial.println(F("Arduino - GPS module"));
}

void loop() {
  // put your main code here, to run repeatedly:
  if(gpsSerial.available() > 0){
    if(gps.encode(gpsSerial.read())){
      if(gps.location.isValid()){
        Serial.print(F("- latitude: "));
        Serial.println(gps.location.lat());

        Serial.print(F("- longitude: "));
        Serial.println(gps.location.lng());

        Serial.print(F("- altitude: "));
        if(gps.altitude.isValid()){
          Serial.pnintln(gps.altitude.meters());
        }else
          Serial.println(F("INVALID"));
        else{
          Serial.println(F("- location: INVALID"));
        }
        
      }
    }
  }
}
