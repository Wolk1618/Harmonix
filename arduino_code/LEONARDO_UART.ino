#include <SoftwareSerial.h>
#include <string.h>

#define SIZE 16

// Choose the pins for the software serial. Do not use the hardware serial pins (0 and 1)
SoftwareSerial mySerial(10, 11); // RX, TX

void setup() {
  // Open serial communications to the computer
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect. Needed for native USB only
  }

  // Set the data rate for the SoftwareSerial port
  mySerial.begin(115200);
}

void loop() {
  if (mySerial.available()) {

    char receivedString[SIZE * 4]; // Assuming each value is a 4-digit number (adjust if needed)
    mySerial.readBytesUntil('\n', receivedString, sizeof(receivedString));

    int values[SIZE]; // Adjust the size based on the number of values in your string

    // Tokenize the input string
    char *token = strtok(receivedString, ";");

    // Loop through the tokens, print them and convert them to integers
    for (int i = 0; i < SIZE && token != NULL; i++) {
      values[i] = atoi(token);
      Serial.print(values[i]);
      Serial.print(" ");
      token = strtok(NULL, ";");
    }
    Serial.print("\n");
  }
}
