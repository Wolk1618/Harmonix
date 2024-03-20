import serial
import threading
import json
import time
import datetime

arduino_com = '/dev/ttyACM3'
esp_com = '/dev/ttyUSB3'
output_file = "test.json" 
run_for_seconds = 2  # Duration to run the threads
label = 5
keep_running = True
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

    #arduino_com = input("Enter the COM port of Arduino (e.g. COM3) : ")
    #esp_com = input("Enter the COM port of ESP (e.g. COM3) : ")

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
    
    # Write data to the JSON file
    with open(output_file, "a") as file:
        json.dump(json_to_write, file)
        file.write(",\n")  # Add newline for each JSON object

if __name__ == "__main__":
    main()
