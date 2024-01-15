#include <SoftwareSerial.h>

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
    Serial.write(mySerial.read());
  }
}
