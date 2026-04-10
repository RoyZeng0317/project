#include "TFT.h"
#include "SPI.h"

#define sc  10
#define dc  9
#define rst 8

TFT TFTscreen = TFT(cs, dc, rst);

void setup() {
  // put your setup code here, to run once:
  TFTscreen.begin();
  TFTscreen.background(0, 0, 0);
  TFTscreen.setTextSize(2);
}

void loop() {
  // put your main code here, to run repeatedly:
  int redRandom = random(0, 255);
  int greendRandom = random(0, 255);
  int blueRandom = random(0, 255);

  TFTscreen.stroke(redRandom, greendRandom, blueRandom);

  TFTscreen.text("Hello, World!", 6, 57);

  delay(200);
}
