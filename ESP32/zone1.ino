// ESP32 z1


#include <Arduino.h>
#if defined(ESP32) || defined(ARDUINO_RASPBERRY_PI_PICO_W)
#include <WiFi.h>
#elif defined(ESP8266)
#include <ESP8266WiFi.h>
#elif __has_include(<WiFiNINA.h>)
#include <WiFiNINA.h>
#elif __has_include(<WiFi101.h>)
#include <WiFi101.h>
#elif __has_include(<WiFiS3.h>)
#include <WiFiS3.h>
#endif

#include "credentials.h" // Custom header
#include <Firebase_ESP_Client.h>
#include <addons/TokenHelper.h> // Provide the token generation process info.
#include <addons/RTDBHelper.h> // Provide the RTDB payload printing info and other helper functions.

// Define Firebase Data object
FirebaseData fbdo;

FirebaseAuth auth;
FirebaseConfig config;

unsigned long sendDataPrevMillis = 0;
#define LED_BUILTIN 2 
#define RELAY 4 

// Relay state
#define ON 1
#define OFF 0

String stringValue = " ";
String previous_word = " ";

#if defined(ARDUINO_RASPBERRY_PI_PICO_W)
  WiFiMulti multi;
#endif

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);  
  pinMode(RELAY, OUTPUT);  
  Serial.begin(115200);

  #if defined(ARDUINO_RASPBERRY_PI_PICO_W)
    multi.addAP(WIFI_SSID, WIFI_PASSWORD);
    multi.run();
  #else
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  #endif

    Serial.print("Connecting to Wi-Fi");
    unsigned long ms = millis();
    while (WiFi.status() != WL_CONNECTED) {
      Serial.print(".");
      delay(300);
  #if defined(ARDUINO_RASPBERRY_PI_PICO_W)
      if (millis() - ms > 10000)
        break;
  #endif
    }
    Serial.println();
    Serial.print("Connected with IP: ");
    Serial.println(WiFi.localIP());
    Serial.println();

    Serial.printf("Firebase Client v%s\n\n", FIREBASE_CLIENT_VERSION);

    /* Assign the api key (required) */
    config.api_key = API_KEY;

    /* Assign the user sign in credentials */
    auth.user.email = USER_EMAIL;
    auth.user.password = USER_PASSWORD;

    /* Assign the RTDB URL (required) */
    config.database_url = DATABASE_URL;

    /* Assign the callback function for the long running token generation task */
    config.token_status_callback = tokenStatusCallback;  // see addons/TokenHelper.h

    // Comment or pass false value when WiFi reconnection will control by your code or third party library e.g. WiFiManager
    Firebase.reconnectNetwork(true);

    // Since v4.4.x, BearSSL engine was used, the SSL buffer need to be set.
    // Large data transmission may require larger RX buffer, otherwise connection issue or data read time out can be occurred.
    fbdo.setBSSLBufferSize(4096 /* Rx buffer size in bytes from 512 - 16384 */, 1024 /* Tx buffer size in bytes from 512 - 16384 */);

    // Limit the size of response payload to be collected in FirebaseData
    fbdo.setResponseSize(2048);

    Firebase.begin(&config, &auth);

    // The WiFi credentials are required for Pico W
    // due to it does not have reconnect feature.
  #if defined(ARDUINO_RASPBERRY_PI_PICO_W)
    config.wifi.clearAP();
    config.wifi.addAP(WIFI_SSID, WIFI_PASSWORD);
  #endif

    Firebase.setDoubleDigits(5);

    config.timeout.serverResponse = 10 * 1000;
}

void loop() {
  if (Firebase.ready() && (millis() - sendDataPrevMillis > 15000 || sendDataPrevMillis == 0)) {
    sendDataPrevMillis = millis();
    // Serial.printf("Get string... %s\n", Firebase.RTDB.getString(&fbdo, F("/zones/z0-z1")) ? fbdo.to<const char *>() : fbdo.errorReason().c_str());

    // Get String from database
    if (Firebase.RTDB.getString(&fbdo, "/zones/z0-z1")) {
      if (fbdo.dataType() == "string") {
        stringValue = fbdo.stringData();  // Fetch the string data

        Serial.println("Raw value: " + stringValue);
        stringValue = getSecondWord(stringValue);
        Serial.println("First word: " + stringValue);
        
        evaluateData(stringValue);
      }
    } else {
      Serial.println(fbdo.errorReason());
    }
  }
}

void evaluateData(String word) {
  word.trim();

  if (previous_word.equals(word))
    return;

  previous_word = word;
  if (word.equals("car")) {
    // ROTATE SERVO

    digitalWrite(LED_BUILTIN, 1);
    digitalWrite(RELAY, ON);
  } else if (word.equals("bus")) {
    // ROTATE SERVO


    digitalWrite(LED_BUILTIN, 1);
    digitalWrite(RELAY, ON);
  } else if (word.equals("truck")) {
    // ROTATE SERVO
    
    
    digitalWrite(LED_BUILTIN, 1);
    digitalWrite(RELAY, ON);
  } else if (word.equals("motor")) {
    // ROTATE SERVO
    
    
    digitalWrite(LED_BUILTIN, 1);
    digitalWrite(RELAY, ON);
  } else {
    digitalWrite(LED_BUILTIN, 0);
    digitalWrite(RELAY, OFF);
  }
}

String getFirstWord(String raw_data) {
  String getWord = "";
  for (int i = 0; i < raw_data.length() && raw_data[i] != '&'; i++) {
    getWord += raw_data[i];
  }
  return getWord;
}

String getSecondWord(String raw_data) {
  String getWord = "";
  bool found_sign = false;

  for (int i = 0; i < raw_data.length(); i++) {
    if (raw_data[i] == '&') {
      found_sign = true;
      continue;  // Skip '&' and move to the next character
    }
    if (found_sign) {
      getWord += raw_data[i];
    }
  }

  return getWord;
}