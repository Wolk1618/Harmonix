#include <SoftwareSerial.h>
#include <Adafruit_LSM6DS3TRC.h>


#define IMU1_I2C_ADDRESS 0x6A
#define IMU2_I2C_ADDRESS 0x6B

Adafruit_LSM6DS3TRC imu1, imu2;

int index1 = 0;
int index2 = 0;


void setup() {
  Serial.println("Adafruit LSM6DS3TR-C tests");

  if (!imu1.begin_I2C(IMU1_I2C_ADDRESS)) {
    Serial.println("Failed to initialize IMU 1!");
    while (1);
  }

  if (!imu2.begin_I2C(IMU2_I2C_ADDRESS)) {
    Serial.println("Failed to initialize IMU 2!");
    while (1);
  }

  imu1.setAccelDataRate(LSM6DS_RATE_52_HZ);
  imu2.setAccelDataRate(LSM6DS_RATE_52_HZ);
  imu1.setGyroDataRate(LSM6DS_RATE_52_HZ);
  imu2.setGyroDataRate(LSM6DS_RATE_52_HZ);
  Serial.println("Both IMUs working");
}

void loop() {
  readIMUData(imu1, "IMU 1");
  readIMUData(imu2, "IMU 2");

  delay(100); // Adjust the delay if needed
}

void readIMUData(Adafruit_LSM6DS3TRC& imu, const char* name) {
  sensors_event_t accel, gyro, temp;
  imu.getEvent(&accel, &gyro, &temp);

  Serial.print(name);

  /* Display the results (acceleration is measured in m/s^2) */
  Serial.print("\t\tAccel X: ");
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
