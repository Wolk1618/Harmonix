import serial
import multiprocessing
import time
import os
import runpy
import numpy as np

from scipy.interpolate import interp1d

arduino_com = '/dev/ttyACM2'
esp_com = '/dev/ttyUSB2'
running_window = 18  # Size of the running window


# Function to read from serial port and write to a JSON file
def arduino_read_from_port(serial_port, data_arduino, arduino_lock):
    serial_port.flushInput()

    while True:
        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()

            with arduino_lock:
                data_arduino.put(data)
            
    
# Function to read data from ESP
def esp_read_from_port(serial_port, data_esp, esp_lock):    
    serial_port.flushInput()

    while True:
        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()
            if data[0] != 'A' and data[0] != 'B' :
                data = serial_port.readline().decode('utf-8').rstrip()
            
            with esp_lock:
                data_esp.put(data)


def process_esp_raw_data(data_esp, esp_lock, esp_right, esp_left, esp_right_lock, esp_left_lock):

    while True:

        data_bite = None
        with esp_lock:
            if not data_esp.empty():
                data_bite = data_esp.get()

        if data_bite:
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
                if target == 'A':
                    with esp_right_lock:
                        esp_right.put(array)
                        #print('ESP right')
                else:
                    with esp_left_lock:
                        esp_left.put(array)
                        #print('ESP left')
                


def process_arduino_raw_data(data_arduino, arduino_lock, arduino_right, arduino_left, arduino_right_lock, arduino_left_lock):

    while True:
            
        data_bite = None
        with arduino_lock:
            if not data_arduino.empty():
                data_bite = data_arduino.get()

        if data_bite:
            parts = data_bite.split("\t")

            # Extracting values using string manipulation
            target = parts[0].split("IMU ")[1]
            accel_x = float(parts[2].split(": ")[1])
            accel_y = float(parts[3].split(": ")[1])
            accel_z = float(parts[4].split(": ")[1])
            gyro_x = float(parts[6].split(": ")[1])
            gyro_y = float(parts[7].split(": ")[1])
            gyro_z = float(parts[8].split(": ")[1].split(" ")[0])

            #print('Data Arduino')
            if target == 'A':
                with arduino_right_lock:
                    arduino_right.put([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z])
            else:
                with arduino_left_lock:
                    arduino_left.put([accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z])


def pad_tof_data(tof_data, imu_data):
    num_imu_readings = len(imu_data[0])  # Assuming all IMU lists have the same length
    num_tof_readings = len(tof_data[0])

    # Handle the case when TOF readings already match or exceed IMU readings
    if num_imu_readings <= num_tof_readings:
        return tof_data

    interpolated_tof = []
    for tof_reading in tof_data:
        # Interpolating each depth map in the TOF reading
        x_original = np.linspace(0, 1, num_tof_readings)
        x_new = np.linspace(0, 1, num_imu_readings)
        interpolator = interp1d(x_original, tof_reading, axis=0, kind='linear', fill_value='extrapolate')
        interpolated_reading = interpolator(x_new)
        interpolated_tof.append(interpolated_reading)

    return np.array(interpolated_tof).tolist()


def process_data(arduino_right, arduino_left, arduino_right_lock, arduino_left_lock, esp_right, esp_left, esp_right_lock, esp_left_lock, final_esp_right, final_esp_left, final_arduino_right, final_arduino_left, final_arduino_right_lock, final_arduino_left_lock, final_esp_right_lock, final_esp_left_lock):

    tof_data_left = []
    imu_data_left = []
    tof_data_right = []
    imu_data_right = []
    
    while True:

        time.sleep(0.01)

        with esp_right_lock:
            while not esp_right.empty():
                tof_data_right.append(esp_right.get())
        
        with esp_left_lock:
            while not esp_left.empty():
                tof_data_left.append(esp_left.get())

        with arduino_right_lock:
            while not arduino_right.empty():
                imu_data_right.append(arduino_right.get())

        with arduino_left_lock:
            while not arduino_left.empty():
                imu_data_left.append(arduino_left.get())


        if len(tof_data_left) != 0 and len(imu_data_left) != 0:
            #print("Left")
            left_tof_padded = pad_tof_data(tof_data_left, imu_data_left)

            with final_esp_left_lock:
                for data in left_tof_padded :
                    final_esp_left.put(data)

            with final_arduino_left_lock:
                for data in imu_data_left :
                    final_arduino_left.put(data)

            tof_data_left = []
            imu_data_left = []


        if len(tof_data_right) != 0 and len(imu_data_right) != 0:
            #print("Right")
            right_tof_padded = pad_tof_data(tof_data_right, imu_data_right)

            with final_esp_right_lock:
                for data in right_tof_padded :
                    final_esp_right.put(data)

            with final_arduino_right_lock:
                for data in imu_data_right :
                    final_arduino_right.put(data)

            tof_data_right = []
            imu_data_right = []

        
            

def apply_running_window(final_esp_right, final_esp_left, final_arduino_right, final_arduino_left, final_arduino_right_lock, final_arduino_left_lock, final_esp_right_lock, final_esp_left_lock, inference_queue, inference_lock):
    global running_window
    tof_data_left = []
    imu_data_left = []
    tof_data_right = []
    imu_data_right = []

    while True:

        with final_esp_right_lock:
            if not final_esp_right.empty():
                #print("hey")
                tof_data_right.append(final_esp_right.get())

        with final_esp_left_lock:
            if not final_esp_left.empty():
                tof_data_left.append(final_esp_left.get())

        with final_arduino_right_lock:
            if not final_arduino_right.empty():
                imu_data_right.append(final_arduino_right.get())

        with final_arduino_left_lock:
            if not final_arduino_left.empty():
                imu_data_left.append(final_arduino_left.get())

        #print("Left buffer: ", len(tof_data_left))
        #print("Right buffer: ", len(tof_data_right))

        print(len(tof_data_left))
        if len(tof_data_left) >= running_window:
            print("left")
            # Extract the data from the buffer
            X_tof = np.array(tof_data_left[:running_window])
            X_imu = np.array(imu_data_left[:running_window])
            tof_data_left.pop(0)
            imu_data_left.pop(0)
            with inference_lock:
                inference_queue.put(['left', X_tof, X_imu])
            
                
        if len(tof_data_right) >= running_window:
            print("right")
            # Extract the data from the buffer
            X_tof = np.array(tof_data_right[:running_window])
            X_imu = np.array(imu_data_right[:running_window])
            tof_data_right.pop(0)
            imu_data_right.pop(0)
            with inference_lock:
                inference_queue.put(['right', X_tof, X_imu])
 

def print_predictions(prediction_queue, prediction_lock):
    while True:
        with prediction_lock:
            if not prediction_queue.empty():
                prediction = prediction_queue.get()
                print(f"Gesture {prediction[0]} : {prediction[1]}")


def main():

    processes = []
    script_path = os.path.abspath('model_for_inference.py')

    data_arduino = multiprocessing.Queue()
    data_esp = multiprocessing.Queue()
    esp_right = multiprocessing.Queue()
    esp_left = multiprocessing.Queue()
    arduino_right = multiprocessing.Queue()
    arduino_left = multiprocessing.Queue()
    final_esp_right = multiprocessing.Queue()
    final_esp_left = multiprocessing.Queue()
    final_arduino_right = multiprocessing.Queue()
    final_arduino_left = multiprocessing.Queue()
    inference_queue = multiprocessing.Queue()
    prediction_queue = multiprocessing.Queue()

    esp_lock = multiprocessing.Lock()
    arduino_lock = multiprocessing.Lock()
    esp_right_lock = multiprocessing.Lock()
    esp_left_lock = multiprocessing.Lock()
    arduino_right_lock = multiprocessing.Lock()
    arduino_left_lock = multiprocessing.Lock()
    final_arduino_right_lock = multiprocessing.Lock()
    final_arduino_left_lock = multiprocessing.Lock()
    final_esp_right_lock = multiprocessing.Lock()
    final_esp_left_lock = multiprocessing.Lock()
    inference_lock = multiprocessing.Lock()
    prediction_lock = multiprocessing.Lock()

    serial_port_arduino = serial.Serial((arduino_com), 9600, timeout=1)
    serial_port_esp = serial.Serial((esp_com), 115200, timeout=1)

    # Create processes for each micro function
    processes.append(multiprocessing.Process(target=arduino_read_from_port, args=(serial_port_arduino, data_arduino, arduino_lock)))
    processes.append(multiprocessing.Process(target=esp_read_from_port, args=(serial_port_esp, data_esp, esp_lock)))
    processes.append(multiprocessing.Process(target=process_esp_raw_data, args=(data_esp, esp_lock, esp_right, esp_left, esp_right_lock, esp_left_lock)))
    processes.append(multiprocessing.Process(target=process_arduino_raw_data, args=(data_arduino, arduino_lock, arduino_right, arduino_left, arduino_right_lock, arduino_left_lock)))
    processes.append(multiprocessing.Process(target=process_data, args=(arduino_right, arduino_left, arduino_right_lock, arduino_left_lock, esp_right, esp_left, esp_right_lock, esp_left_lock, final_esp_right, final_esp_left, final_arduino_right, final_arduino_left, final_arduino_right_lock, final_arduino_left_lock, final_esp_right_lock, final_esp_left_lock)))
    processes.append(multiprocessing.Process(target=apply_running_window, args=(final_esp_right, final_esp_left, final_arduino_right, final_arduino_left, final_arduino_right_lock, final_arduino_left_lock, final_esp_right_lock, final_esp_left_lock, inference_queue, inference_lock)))
    processes.append(multiprocessing.Process(target=runpy.run_path, args=(script_path,), kwargs={'args': (inference_queue, inference_lock, prediction_queue, prediction_lock)}))
    processes.append(multiprocessing.Process(target=print_predictions, args=(prediction_queue, prediction_lock)))

    print("\nHarmonix started !\n")

    # Start all processes
    for p in processes:
        p.start()

    # Wait for user to stop the programme
    while True:
        user_input = input("Press Q to quit: ")
        if user_input.lower() == "q":
            break

    # Stop all processes
    for p in processes:
        p.join()


if __name__ == "__main__":
    main()
