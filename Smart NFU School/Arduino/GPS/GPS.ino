#include<TinyGPS++.h>
#include<SoftwareSerial.h>
SoftwareSerial gpsSerial(4,3);
Tinygpslus gps;


void setup() {
  serial.begin(9600);
  gpsSerial.begin(9600);
serial.println("GPS定位系統啟動中...");
}

void loop() {
  while(gpsSerial.available()>0){
    gps.encode(gpsSerial.read());
if(gps.location.isUpdated()){
  Serial.print("====目前位置====");
serial.print("Latitude:");
  serial.println(gps.location.lat(),6);

  serial.print("Longitude:");
  serial.println(gps.location.lat(),6);

  serial.print("Satellites:");
  serial.println(gps.satellites.value());

  Serial.print("Time:");
Serial.print(gps.time.hour());
Serial.print(":");
  Serial.print(gps.time.minute());
  Serial.print(":");
  Serial.println(gps.time.second());

  serial.println("=================");
  serial.println();
    }
    
   }
}
