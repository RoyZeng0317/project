#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2); // sethe LCD address to 0x27 for a 16 chars and line display

char response = {"520", "521", "I miss you"};

void setup() {
  // put your setup code here, to run once:
  lcd.init(); // initialize the lcd
  // lcd.begin(16, 2);
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Hello, world!");
  
  lcd.setCursor(0, 1);
  lcd.print("BBC Call");
}

void loop() {

}
