#include <SoftwareSerial.h>
 
#define SIZE 64
 
SoftwareSerial mySerial(10, 11); // RX, TX
 
int values1[SIZE];
 
int values2[SIZE];
 
int index1 = 0;
 
int index2 = 0;
 
void setup() {
 
  Serial.begin(19200);
 
  mySerial.begin(19200);
 
}
 
void loop() {
    static String currentData;  // Accumulates data for a batch
    static bool isBatchStart = true;  // Flag to identify the start of a new batch
 
    while (mySerial.available()) {
        char inChar = (char)mySerial.read();
 
        // Add character to the current data
        currentData += inChar;
 
        // Check for the start of a new batch
        if (isBatchStart && (inChar == 'A' || inChar == 'B')) {
            currentData = inChar;  // Reset currentData with the batch identifier
            isBatchStart = false;  // Now we're inside a batch
        }
       
        // Check for the end of a batch
        if (inChar == ';' && currentData.endsWith("Z;")) {
            processChunk(currentData);  // Process the complete batch
            currentData = "";  // Reset for the next batch
            isBatchStart = true;  // Ready for the next batch
        }
    }
}
 
void processChunk(String chunk) {
    if (chunk.startsWith("A") || chunk.startsWith("B")) {
        char sensorID = chunk.charAt(0);
 
 
        chunk = chunk.substring(1); // Remove the sensor ID character
        chunk.trim(); // Remove any leading or trailing whitespace
 
        int arrayIndex = 0;
        int* valuesArray = (sensorID == 'A') ? values1 : values2;
 
        int startPos = 0;
        int endPos = chunk.indexOf(';');
 
        while (endPos != -1) {
            String valueString = chunk.substring(startPos, endPos);
            valueString.trim(); // Remove any whitespace around the number
            if (valueString == "Z") {  // Check if the value is 'Z'
                break;  // Break the loop if 'Z' is found
            }
            int value = valueString.toInt();
            valuesArray[arrayIndex++] = value;
 
            startPos = endPos + 1; // Move past the semicolon
            endPos = chunk.indexOf(';', startPos); // Find the next semicolon
        }
 
        // If we've received all measurements for a sensor, print them
        if (arrayIndex == SIZE) {
            printValues(valuesArray, SIZE, (sensorID == 'A') ? "Sensor 1" : "Sensor 2");
        }
    }
}
 
void printValues(int values[], int size, String label) {
    Serial.println(label + " Depth Map:");
    for (int i = 0; i < size; i++) {
        Serial.print(values[i]);
        Serial.print("\t"); // Use tab for spacing
        if ((i + 1) % 8 == 0) {
            Serial.println(); // Move to a new line after every 8 values
        }
    }
    Serial.println(); // Extra line for separation
}