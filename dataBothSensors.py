import serial
import threading
import json
import time
import datetime

arduino_com = 'COM9'
esp_com = 'COM12'
run_for_seconds = 5  # Duration to run the threads
keep_running = True # Global variable to control the running of threads
global_json = []
label = 1 # to be changed depending on the movement realized


# Function to read from serial port and write to a JSON file
def arduino_read_from_port(serial_port):
    global keep_running
    global json_to_write
    while keep_running:
        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()
            print(f"Data from {serial_port.port}: {data}")
            # Prepare the data to write to the file
            parts = data.split("\t")

            # Extracting values using string manipulation
            target = float(parts[0].split("IMU ")[1])
            accel_x = float(parts[2].split(": ")[1])
            accel_y = float(parts[3].split(": ")[1])
            accel_z = float(parts[4].split(": ")[1])
            gyro_x = float(parts[6].split(": ")[1])
            gyro_y = float(parts[7].split(": ")[1])
            gyro_z = float(parts[8].split(": ")[1].split(" ")[0])
            
            data_to_write = {
                "IMU": target,
                "accel_x": accel_x,
                "accel_y": accel_y,
                "accel_z": accel_z,
                "gyro_x": gyro_x,
                "gyro_y": gyro_y,
                "gyro_z": gyro_z,
            }
            
            global_json.append(data_to_write)
            
            
             
                
# Function to read from serial port and write to a JSON file
def esp_read_from_port(serial_port):
    global keep_running
    global json_to_write
    while keep_running:
        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()
            
            # Prepare the data to write to the file
            target = data[0]
            clean_data = data[1:-2]
            print(f"Data from {serial_port.port}: {clean_data}")
            
            data_to_write = {
                "TOF": target,
                "data": clean_data,
            }
            
            global_json.append(data_to_write)
            

def main():
    global keep_running
    global json_to_write
    output_file = "output_data.json"  # Name of the JSON file to store the data

    # Set up COM9 at 1200 baud
    serial_port_ard = serial.Serial(arduino_com, 9600, timeout=1)
    # Set up COM12 at 115200 baud
    serial_port_esp = serial.Serial(esp_com, 115200, timeout=1)

    # Create threads for each COM port
    thread_com9 = threading.Thread(target=arduino_read_from_port, args=(serial_port_ard,))
    thread_com12 = threading.Thread(target=esp_read_from_port, args=(serial_port_esp,))


    # Start threads
    thread_com9.start()
    thread_com12.start()

    # Run for a specified duration
    time.sleep(run_for_seconds)

    # Signal threads to stop
    keep_running = False

    # Wait for threads to finish
    thread_com9.join()
    thread_com12.join()
    
    json_to_write = {
        "timestamp": datetime.datetime.now().isoformat(),
        "label": label,
        "data": global_json
    }
    
    # Write data to the JSON file
    with open(output_file, "a") as file:
        json.dump(json_to_write, file)
        file.write("\n")  # Add newline for each JSON object

    print("Data collection completed.")

if __name__ == "__main__":
    main()
