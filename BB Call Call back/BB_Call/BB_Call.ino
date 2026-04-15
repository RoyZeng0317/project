#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <SoftwareSerial.h>

LiquidCrystal_I2C lcd(0x27, 16, 2); // sethe LCD address to 0x27 for a 16 chars and line display

Strin[] response = {"520", "521", "I miss you"};

SoftwareSerial BT(10, 11);

String received = "";

void setup() {
  // put your setup code here, to run once:
  lcd.init(); // initialize the lcd
  lcd.backlight();

  BT.begin(9600);
  Serial.begin(9600);

  lcd.setCursor(0, 0);
  lcd.print("BB Call Ready");  
}

void loop() {
  while(BT.available()){
    char c = BT.read();
    received += c;

    if(c == '\n'){
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Msg:");

      lcd.setCursor(0, 1);
      lcd.print(received);

      BT.println("Received: " + received);

      received = "";
    }
  }
}
