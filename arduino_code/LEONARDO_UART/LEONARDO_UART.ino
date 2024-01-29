#include <SoftwareSerial.h>

#define SIZE 64

SoftwareSerial mySerial(10, 11); // RX, TX

int values1[SIZE]; 
int values2[SIZE];
int index1 = 0;
int index2 = 0;

void setup() {
  Serial.begin(115200);
  mySerial.begin(115200);
}

void loop() {
  if (mySerial.available()) {
    String receivedChunk = mySerial.readStringUntil(';');
    processChunk(receivedChunk);
  }
}

void processChunk(String chunk) {
  if (chunk.length() > 1) { // Ensure chunk is not empty
    char sensorID = chunk.charAt(0); // First character identifies the sensor
    int value = chunk.substring(1).toInt(); // Convert the rest to integer
    
    if (sensorID == 'A' && index1 < SIZE) {
      values1[index1++] = value;
      if (index1 == SIZE) {
        printValues(values1, SIZE, "Sensor 1");
        index1 = 0; // Reset for next batch
      }
    } else if (sensorID == 'B' && index2 < SIZE) {
      values2[index2++] = value;
      if (index2 == SIZE) {
        printValues(values2, SIZE, "Sensor 2");
        index2 = 0; // Reset for next batch
      }
    }
  }
}

void printValues(int values[], int size, String label) {
  Serial.println(label + " Depth Map:");
  for (int i = 0; i < size; i++) {
    Serial.print(values[i]);
    Serial.print("\t"); // Use tab for spacing, adjust as needed for alignment

    // After every 8 values, move to a new line to create the 8x8 grid
    if ((i + 1) % 8 == 0) {
      //Serial.println(); // Move to new line
    }
  }
  Serial.println(); // Add an extra line for separation between batches or sensors
}
