const int IR1=2;
const int IR2=3;
int carCount =0;
int state=0;
void setup() {
  pinMode(IR1,input);
pinMode(IR2,input);
serial.begin(9600)
serial.println("車輛計數系統啟動");
}

void loop() {
 int sensor1=digitlRead(IR1);
int sensor2=digitlRead(IR2);

if(sensor2==LOW&&state==1)
{
  state=1;
}
if (sensor2==LOW&&state==1)
{
  carcount++;
  serial.print("車輛進入，目前車數:");
  serial.println(caeCount);
  delay(500);
  state=0;
  
}


  if (sensor1==LOW&&state==2)
{
  if(carCount>0)
  {
    carcount--;
  }
serial.println("車輛離開，目前車數:");
  serial.println(carcount);
  delay(500);
  state=0;
 }


 }
