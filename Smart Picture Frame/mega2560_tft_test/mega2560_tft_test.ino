#include <Adafruit_GFX.h>    // Core graphics library
#include <MCUFRIEND_kbv.h> // Hardware-specific library

#define    BLACK   0x0000
#define BLUE    0x001F
#define RED     0xF800
#define GREEN   0x07E0
#define CYAN    0x07FF
#define MAGENTA 0xF81F
#define YELLOW  0xFFE0
#define WHITE   0xFFFF

MCUFRIEND_kbv tft;

void setup() {
    // put your setup code here, to run once:
    tft.reset();
    tft.begin(tft.readID());
    tft.fillScreen(BLACK);
    uint16_t TFTWIDTH = tft.width();
    uint16_t TFTHEIGHT = tft.height();
    tft.fillRect(0, 0, TFTWIDTH / 2, TFTHEIGHT / 2, RED);             //upper left
    tft.fillRect(TFTWIDTH / 2, 0, TFTWIDTH / 2, TFTHEIGHT / 2, GREEN); //upper right
    tft.fillRect(TFTWIDTH / 2, TFTHEIGHT / 2, TFTWIDTH / 2, TFTHEIGHT / 2, BLUE); //lower right
    tft.fillRect(0, TFTHEIGHT / 2, TFTWIDTH / 2, TFTHEIGHT / 2, YELLOW); //lower left

}

void loop()
{
    // put your main code here, to run repeatedly:

}