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

    char receivedString[2 * SIZE * 4]; // Assuming each value is a 4-digit number (adjust if needed)
    mySerial.readBytesUntil('\n', receivedString, sizeof(receivedString));
    //strcpy(receivedString, "1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; - 2; 2; 2; 2; 2; 2; 2; 2; 2; 2; 2; 2; 2; 2; 2; 2;");

    int values1[SIZE]; 
    int values2[SIZE];

    char *string1 = strtok(receivedString, "-");
    char *string2 = strtok(NULL, "-");

    // Tokenize the input string
    char *token1 = strtok(string1, ";");
    Serial.print("Data from first sensor :");
    // Loop through the tokens, print them and convert them to integers
    for (int i = 0; i < SIZE && token1 != NULL; i++) {
      values1[i] = atoi(token1);
      Serial.print(values1[i]);
      Serial.print(" ");
      token1 = strtok(NULL, ";");
    }
    Serial.print("\n");

    char *token2 = strtok(string2, ";");
    Serial.print("Data from second sensor :");
    // Loop through the tokens, print them and convert them to integers
    for (int i = 0; i < SIZE && token2 != NULL; i++) {
      values2[i] = atoi(token2);
      Serial.print(values2[i]);
      Serial.print(" ");
      token2 = strtok(NULL, ";");
    }
    Serial.print("\n");
  }
}
