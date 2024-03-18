import keras
import serial
import threading
import json
import time
import datetime

import numpy as np

arduino_com = '/dev/ttyACM0'
esp_com = '/dev/ttyUSB0'
model_file = "Harmonix_v1.hdf5"
running_window = 2  # Duration of the running window
data_arduino = []
data_esp = []


# Function to read from serial port and write to a JSON file
def arduino_read_from_port(serial_port):
    global keep_running
    global data_arduino
    global data_esp

    serial_port.flushInput()

    while keep_running:
        if serial_port.in_waiting:

            data = serial_port.readline().decode('utf-8').rstrip()
            #print(f"Data from {serial_port.port}: {data}")

            data_arduino.append(data)
            
    

# Function to read from serial port and write to a JSON file
def esp_read_from_port(serial_port):
    global keep_running
    global data_arduino
    global data_esp
    
    serial_port.flushInput()

    while keep_running:
        if serial_port.in_waiting:
            
            # Prepare the data to write to the file
            data = serial_port.readline().decode('utf-8').rstrip()
            if data[0] != 'A' and data[0] != 'B' :
                data = serial_port.readline().decode('utf-8').rstrip()
            
            print(f"Data from {serial_port.port}: {data}")
            
            data_esp.append(data)


def main():
    global keep_running
    global data_arduino
    global data_esp

    raw_data = {
        'A' : {
            "TOF": [],
            "IMU": []
        },
        'B' : {
            "TOF": [],
            "IMU": []
        }   
    }


    serial_port_arduino = serial.Serial((arduino_com), 9600, timeout=1)
    serial_port_esp = serial.Serial((esp_com), 115200, timeout=1)

    # Create threads for each COM port
    thread_arduino = threading.Thread(target=arduino_read_from_port, args=(serial_port_arduino, ))
    thread_esp = threading.Thread(target=esp_read_from_port, args=(serial_port_esp, ))
    
    print("Data collection will start in :")
    time.sleep(0.5)
    print("3")
    time.sleep(0.5)
    print("2")
    time.sleep(0.5)
    print("1")
    time.sleep(0.5)
    print("\nData collection started\n")
    

    thread_arduino.start()
    thread_esp.start()

    # Run for a specified duration
    time.sleep(run_for_seconds)

    # Signal threads to stop
    keep_running = False

    thread_arduino.join()
    thread_esp.join()

    print("\nData collection completed.\n")

    for data_bite in data_esp :

        target = data_bite[0]
        clean_data = data_bite[1:-2]
        containsA = clean_data.count('A')
        containsB = clean_data.count('B')
        
        if containsA :
            target = 'A'
            clean_data = clean_data.split('A')[1]
            print('overwrite flushed')
        elif containsB :
            target = 'B'
            clean_data = clean_data.split('B')[1] 
            print('overwrite flushed')        
        
        # Divide in substrings and convert each substring to integer
        substrings = clean_data.split(';')
        array = [int(x) for x in substrings if x != '']

        if len(array) != 64 :
            print('outlier flushed')
        else :
            raw_data[target]['TOF'].append({
                "depth_map": array,
            })

    for data_bite in data_arduino :

        parts = data_bite.split("\t")

        # Extracting values using string manipulation
        target = parts[0].split("IMU ")[1]
        accel_x = float(parts[2].split(": ")[1])
        accel_y = float(parts[3].split(": ")[1])
        accel_z = float(parts[4].split(": ")[1])
        gyro_x = float(parts[6].split(": ")[1])
        gyro_y = float(parts[7].split(": ")[1])
        gyro_z = float(parts[8].split(": ")[1].split(" ")[0])

        raw_data[target]['IMU'].append({
            "accel_x": accel_x,
            "accel_y": accel_y,
            "accel_z": accel_z,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
        })

    #label = int(input("Enter the label of the recorded sample : "))
    #output_file = input("Enter the file in which you want the datapoint to be stored : ")
    timestamp = datetime.datetime.now().isoformat()

    json_to_write = {
        "timestamp": timestamp,
        "label": label,
        "left": raw_data["B"],
        "right": raw_data["A"]
    }

if __name__ == "__main__":
    main()


# Load the model
model = torch.load(model_file)

# Prepare the input data (IMU and TOF)
imu_data = ...  # Replace with your IMU data
tof_data = ...  # Replace with your TOF data

# Perform inference
with keras.backend.get_session().graph.as_default():
    input_data = np.concatenate((imu_data, tof_data), axis=1)
    output = model.predict(input_data)

    # Evaluate the model on the test data
    predictions = model.predict([X_test_tof, X_test_imu])
    y_pred = np.argmax(predictions, axis=1)
    y_test = np.argmax(y_test, axis=1)
    confidence = np.max(predictions, axis=1)

    y_pred[confidence < 0.8] = 0

# Process the output
# ...

# Print the result
print(output)