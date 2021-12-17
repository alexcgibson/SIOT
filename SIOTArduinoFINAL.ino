#ifdef ESP32
  #include <WiFi.h>
#endif
#include <Wire.h>
#include "DHT.h"
#include <HTTPClient.h>
#include <Arduino_JSON.h>

//connect to phone hotspot
const char* ssid     = "alexsiphone";
const char* password = "12345678";

unsigned long lastTime = 0;
unsigned long timerDelay = 20000;

String jsonBuffer;

const char* resource = "/trigger/dht_readings/with/key/cccqE3_I71i6YOO13fh9T6mAd83TgrMy_sOhAupspnl";

// Maker Webhooks IFTTT
const char* server = "maker.ifttt.com";

// Time to sleep
// Conversion factor for micro seconds to seconds
uint64_t uS_TO_S_FACTOR = 1000000;
// sleep for 1 minute
uint64_t TIME_TO_SLEEP = 60;

#define DHTPIN 4
#define DHTTYPE DHT22   // DHT 22 initiate
#define Photoresistor 2 //photoresister initiate

DHT dht(DHTPIN, DHTTYPE);

int brightness = analogRead(Photoresistor); //read photoresistor and assign to variable

void setup() {
  Serial.begin(115200);
  
  dht.begin();

  initWifi();
  makeIFTTTRequest();
  
  #ifdef ESP32
    // enable timer deep sleep
    esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * uS_TO_S_FACTOR);    
    Serial.println("Going to sleep now");
    // start deep sleep for 60 seconds
    esp_deep_sleep_start();
  #else
    // Deep sleep mode 1 minute
    Serial.println("Going to sleep now");
    ESP.deepSleep(TIME_TO_SLEEP * uS_TO_S_FACTOR); 
  #endif
}

void loop() {
  // sleeping so wont get here 
}

// Establish a Wi-Fi connection with phone hotspot
void initWifi() {
  Serial.print("Connecting to: "); 
  Serial.print(ssid);
  WiFi.begin(ssid, password);  

  int timeout = 10 * 4; // 10 seconds
  while(WiFi.status() != WL_CONNECTED  && (timeout-- > 0)) {
    delay(250);
    Serial.print(".");
  }
  Serial.println("");

  if(WiFi.status() != WL_CONNECTED) {
     Serial.println("Failed to connect, going back to sleep");
  }

  Serial.print("WiFi connected in: "); 
  Serial.print(millis());
  Serial.print(", IP address: "); 
  Serial.println(WiFi.localIP());
}

// Make an HTTP request to the IFTTT web service
void makeIFTTTRequest() {
  Serial.print("Connecting to "); 
  Serial.print(server);
  
  WiFiClient client;
  int retries = 5;
  while(!!!client.connect(server, 80) && (retries-- > 0)) {
    Serial.print(".");
  }
  Serial.println();
  if(!!!client.connected()) {
    Serial.println("Failed to connect...");
  }
  
  Serial.print("Request resource: "); 
  Serial.println(resource);

  // Read sensor values
  String jsonObject = String("{\"value1\":\"") + 
  dht.readHumidity() + "\",\"value2\":\"" + 
  dht.readTemperature() + "\",\"value3\":\"" + 
  brightness + "\"}";
                      
  client.println(String("POST ") + resource + " HTTP/1.1");
  client.println(String("Host: ") + server); 
  client.println("Connection: close\r\nContent-Type: application/json");
  client.print("Content-Length: ");
  client.println(jsonObject.length());
  client.println();
  client.println(jsonObject);
        
  int timeout = 5 * 10; // 5 seconds             
  while(!!!client.available() && (timeout-- > 0)){
    delay(100);
  }
  if(!!!client.available()) {
    Serial.println("No response...");
  }
  while(client.available()){
    Serial.write(client.read());
  }
  
  Serial.println("\nclosing connection");
  client.stop(); 
}
