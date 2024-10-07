//------------需要的库------------//
#include <TFT_eSPI.h>
#include <SPI.h>
#include <WiFi.h>
#include <TJpg_Decoder.h>
TFT_eSPI tft = TFT_eSPI(); 
//------在这里定义你的各种参数-------//
const char* ssid     = "Visual aids"; //填写你的wifi名字
const char* password = "kust232751"; //填写你的wifi密码
const char* service_ip = "192.168.220.176"; //上位机IP地址
int httpPort = 5000; //设置上位机端口

//----下面的参数用于loadingcartoon函数-----//

//-------以下参数用于收发图片--------------//
WiFiClient client; //初始化一个客户端对象
TaskHandle_t loading = NULL;
uint8_t buff[7000] PROGMEM = {0}; //每一帧的临时缓存
uint8_t img_buff[40000] PROGMEM = {0}; //用于存储tcp传过来的图片，注意图片大小不要超出内存，分辨率高的屏幕可以扩容
uint16_t size_count = 0; //计算一帧的字节大小
uint16_t read_count, s_time, e_time, total_count = 0;
uint8_t length[2];

//------------------------------------//
bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t* bitmap) //jpg解码回调函数
{
  if (y >= tft.height()) return 0;
  tft.pushImage(x, y, w, h, bitmap);
  // Return 1 to decode next block
  return 1;
}

void setup() {
  Serial.begin(115200);
  tft.begin();
  tft.setRotation(3); //竖屏240x240
  tft.fillScreen(TFT_WHITE); //白屏
  tft.setTextColor(TFT_BLACK, TFT_WHITE);
  tft.fillRect(20, 100, 200, 20, TFT_WHITE);
  tft.drawString("connecting..", 30, 150, 4);
  WiFi.begin(ssid, password); //连接wifi
  delay(1000); //等待1秒
  while (WiFi.status() != WL_CONNECTED) {
    for (byte n = 0; n < 10; n++) { //每500毫秒检测一次状态
      //loading(50);
      delay(500);
    }
  }

  if (WiFi.status() == WL_CONNECTED) //判断如果wifi连接成功
  { 
    client.connect(service_ip, httpPort); //连接到上位机
    Serial.println("WiFi is connected!");
    Serial.print("SSID: ");
    Serial.println(WiFi.SSID());
    IPAddress ip = WiFi.localIP();
    Serial.print("IP Address: ");
    Serial.println(ip);
  } else {
    Serial.printf("Connect failed");
  }
  
  tft.drawString("connected....", 30, 150, 4);
  delay(2000);
  tft.fillScreen(TFT_BLACK);
  TJpgDec.setJpgScale(1);
  TJpgDec.setSwapBytes(true);
  TJpgDec.setCallback(tft_output); //解码成功回调函数
}

//-------------------------------------------------//
void loop() {
  
  client.write("CPP");
  delay(1);
  
  while (1) {
    if (client.available()) {
      read_count = client.read(length, 1024);
      size_count = length[0] + length[1] * 0x100;
      Serial.println(size_count);
      read_count = 0;
      client.write("PY");
      while (total_count < size_count) {
        if (client.available()) {
          read_count = client.read(buff, 7000); //向缓冲区读取数据
          memcpy(&img_buff[total_count], buff, read_count); //将读取的buff字节地址复制给img_buff数组 
          total_count += read_count;
        }
      }
      Serial.println(total_count);
      TJpgDec.drawJpg(0, 0, img_buff, sizeof(img_buff)); //将jpg图片解码为bmp
      memset(&img_buff, 0, sizeof(img_buff)); //清空buff
      total_count = 0;
    } else {
      continue;
    }
    break;
  }
}
