#include <SoftwareSerial.h>
#include <Adafruit_LSM6DS3TRC.h>

#define SIZE 64
#define IMU1_I2C_ADDRESS 0x6A
#define IMU2_I2C_ADDRESS 0x6B

Adafruit_LSM6DS3TRC imu1, imu2;
SoftwareSerial mySerial(10, 11); // RX, TX

int values1[SIZE]; 
int values2[SIZE];
int index1 = 0;
int index2 = 0;


void setup() {
  Serial.begin(115200);
  mySerial.begin(115200);

  Serial.println("adafruit LSM6DS3TR-C tests");
  
  if (!imu1.begin_I2C(IMU1_I2C_ADDRESS)) {
    Serial.println("Failed to initialize IMU 1!");
    while (1);
  }

  if (!imu2.begin_I2C(IMU2_I2C_ADDRESS)) {
    Serial.println("Failed to initialize IMU 2!");
    while (1);
  }

  Serial.println("Both IMUs working");
}

void loop() {
  if (mySerial.available()) {
    String receivedChunk = mySerial.readStringUntil(';');
    processChunk(receivedChunk);
  }

  //readIMUData(imu1, "IMU 1"); // UNCOMMENT TO USE IMU
  //readIMUData(imu2, "IMU 2");

  //delay(100); // Adjust the delay if needed
}

void readIMUData(Adafruit_LSM6DS3TRC& imu, const char* name) {
  sensors_event_t accel, gyro, temp;
  imu.getEvent(&accel, &gyro, &temp);
  
  Serial.print(name);

  /* Display the results (acceleration is measured in m/s^2) */
  Serial.print("\t\taccel X: ");
  Serial.print(accel.acceleration.x);
  Serial.print(" \tY: ");
  Serial.print(accel.acceleration.y);
  Serial.print(" \tZ: ");
  Serial.print(accel.acceleration.z);
  Serial.println(" m/s^2 ");

  /* Display the results (rotation is measured in rad/s) */
  Serial.print("\t\tGyro X: ");
  Serial.print(gyro.gyro.x);
  Serial.print(" \tY: ");
  Serial.print(gyro.gyro.y);
  Serial.print(" \tZ: ");
  Serial.print(gyro.gyro.z);
  Serial.println(" radians/s ");
  Serial.println();
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
