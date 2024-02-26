import serial
import threading
import json
import time
import datetime
import platform

arduino_com = '/dev/ttyACM0'
esp_com = '/dev/ttyUSB0'
output_file = "output_data.json"  # Name of the JSON file to store the data
run_for_seconds = 2  # Duration to run the threads
label = 1 # to be changed depending on the movement realized


def convert_com_to_tty(com_port):
    if platform.system() == 'Windows':
        # For Windows, simply return the COM port as is
        return com_port
    elif platform.system() == 'Linux':
        # For Linux, convert COM port to tty port
        try:
            # Assuming com_port is something like "COM3"
            com_number = int(com_port[3:])
            tty_port = f"/dev/ttyUSB{com_number - 1}"
            return tty_port
        except ValueError:
            # Handle the case where the COM port is not in the expected format
            raise ValueError("Invalid COM port format for Linux")
    else:
        raise NotImplementedError("This script is not implemented for the current operating system")


# Function to read from serial port and write to a JSON file
def arduino_read_from_port(serial_port, data_arduino):
    
    # Wait for Arduino to be ready 
    while not(serial_port.in_waiting):
        pass

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
    
    data_arduino.append({
        "accel_x": accel_x,
        "accel_y": accel_y,
        "accel_z": accel_z,
        "gyro_x": gyro_x,
        "gyro_y": gyro_y,
        "gyro_z": gyro_z,
    })
    data_arduino.append(target)
                
# Function to read from serial port and write to a JSON file
def esp_read_from_port(serial_port, data_esp):
    
    # Wait for ESP to be ready 
    while not(serial_port.in_waiting):
        pass

    # Prepare the data to write to the file
    data = serial_port.readline().decode('utf-8').rstrip()
    target = data[0]
    clean_data = data[1:-2]
    #print(f"Data from {serial_port.port}: {clean_data}")
    
    data_esp.append({
        "data": clean_data,
    })            
    data_esp.append(target)

def main():
    keep_running = True
    start_time = time.time()
    data_left = []
    data_right = []
    data_arduino = []
    data_esp = []

    arduino_com = input("Enter the COM port of Arduino (e.g. COM3) : ")
    esp_com = input("Enter the COM port of ESP (e.g. COM3) : ")

    serial_port_arduino = serial.Serial((arduino_com), 9600, timeout=1)
    serial_port_esp = serial.Serial((esp_com), 115200, timeout=1)

    while keep_running:
        # Create threads for each COM port
        thread_arduino = threading.Thread(target=arduino_read_from_port, args=(serial_port_arduino, data_arduino))
        thread_esp = threading.Thread(target=esp_read_from_port, args=(serial_port_esp, data_esp))

        # Start threads
        thread_arduino.start()
        thread_esp.start()

        # Wait for threads to finish
        thread_arduino.join()
        thread_esp.join()

        sensor_arduino = data_arduino.pop()
        sensor_esp = data_esp.pop()

        if sensor_esp != sensor_arduino :
            print("Wrong order of sensors")
            keep_running = False
        elif(sensor_esp == 'A') :
            data_right.append({
                "TOF": data_esp.pop(),
                "IMU": data_arduino.pop()
            })
        else :
            data_left.append({
                "TOF": data_esp.pop(),
                "IMU": data_arduino.pop()
            })

        # Signal threads to stop
        if time.time() - start_time >= run_for_seconds :
            keep_running = False

    print("Data collection completed.")
    label = int(input("Enter the label of the recorded sample : "))
    #output_file = input("Enter the file in which you want the datapoint to be stored : ")

    json_to_write = {
        "timestamp": datetime.datetime.now().isoformat(),
        "label": label,
        "left": data_left,
        "right": data_right
    }
    
    # Write data to the JSON file
    with open(output_file, "a") as file:
        json.dump(json_to_write, file)
        file.write("\n")  # Add newline for each JSON object

if __name__ == "__main__":
    main()
