import serial
import threading
import json
import time
import datetime

arduino_com = '/dev/ttyACM0'
esp_com = '/dev/ttyUSB0'
output_file = "output_data.json" 
run_for_seconds = 2  # Duration to run the threads
label = 1
keep_running = True
data_arduino = []
data_esp = []


# Function to read from serial port and write to a JSON file
def arduino_read_from_port(serial_port):
    global keep_running
    global data_arduino
    global data_esp

    while keep_running:
        if serial_port.in_waiting:

            data = serial_port.readline().decode('utf-8').rstrip()
            #print(f"Data from {serial_port.port}: {data}")

            # Prepare the data to write to the file
            parts = data.split("\t")

            # Extracting values using string manipulation
            target = parts[0].split("IMU ")[1]
            accel_x = float(parts[2].split(": ")[1])
            accel_y = float(parts[3].split(": ")[1])
            accel_z = float(parts[4].split(": ")[1])
            gyro_x = float(parts[6].split(": ")[1])
            gyro_y = float(parts[7].split(": ")[1])
            gyro_z = float(parts[8].split(": ")[1].split(" ")[0])

            data_arduino.append([target, {
                "accel_x": accel_x,
                "accel_y": accel_y,
                "accel_z": accel_z,
                "gyro_x": gyro_x,
                "gyro_y": gyro_y,
                "gyro_z": gyro_z,
            }])


# Function to read from serial port and write to a JSON file
def esp_read_from_port(serial_port):
    global keep_running
    global data_arduino
    global data_esp
    
    while keep_running:
        if serial_port.in_waiting:

            # Prepare the data to write to the file
            data = serial_port.readline().decode('utf-8').rstrip()
            target = data[0]
            clean_data = data[1:-2]
            #print(f"Data from {serial_port.port}: {clean_data}")

            # Divide in substrings
            substrings = clean_data.split(';')

            # Convert each substring to integer and create list of integers
            array = [int(x) for x in substrings if x != '']

            data_esp.append([target, {
                "depth_map": array,
            }])


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

    #arduino_com = input("Enter the COM port of Arduino (e.g. COM3) : ")
    #esp_com = input("Enter the COM port of ESP (e.g. COM3) : ")

    serial_port_arduino = serial.Serial((arduino_com), 9600, timeout=1)
    serial_port_esp = serial.Serial((esp_com), 115200, timeout=1)

    # Create threads for each COM port
    thread_arduino = threading.Thread(target=arduino_read_from_port, args=(serial_port_arduino, ))
    thread_esp = threading.Thread(target=esp_read_from_port, args=(serial_port_esp, ))

    thread_arduino.start()
    thread_esp.start()

    # Run for a specified duration
    time.sleep(run_for_seconds)

    # Signal threads to stop
    keep_running = False

    thread_arduino.join()
    thread_esp.join()

    print("Data collection completed.")
    label = int(input("Enter the label of the recorded sample : "))
    #output_file = input("Enter the file in which you want the datapoint to be stored : ")
    timestamp = datetime.datetime.now().isoformat()

    for data_bite in data_esp :
        raw_data[data_bite[0]]['TOF'].append(data_bite[1])

    for data_bite in data_arduino :
        raw_data[data_bite[0]]['IMU'].append(data_bite[1])

    json_to_write = {
        "timestamp": timestamp,
        "label": label,
        "left": raw_data["B"],
        "right": raw_data["A"]
    }
    
    # Write data to the JSON file
    with open(output_file, "a") as file:
        json.dump(json_to_write, file)
        file.write("\n")  # Add newline for each JSON object

if __name__ == "__main__":
    main()
