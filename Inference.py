import serial
import multiprocessing
import time
import runpy
import numpy as np

from tensorflow.keras.models import load_model
from scipy.interpolate import interp1d

arduino_com = '/dev/ttyACM3'
esp_com = '/dev/ttyUSB3'
running_window = 18  # Size of the running window

model_file = 'final_model.h5'

class Model:
    def __init__(self, model_path):
        self.model = load_model(model_path)

    def format_data(self, X_tof, X_imu):
        #X_tof = np.reshape(X_tof, (1, 18, 8, 8))
        #X_imu = np.reshape(X_imu, (1, 18, 6))
        #X_tof = np.transpose(X_tof, (0, 2, 3, 1))
        #X_imu = np.transpose(X_imu, (0, 2, 1))
        X_tof = np.reshape(X_tof, (18, 8, 8))
        X_imu = np.reshape(X_imu, (18, 6))
        X_tof = np.transpose(X_tof, (1, 2, 0))
        X_imu = np.transpose(X_imu, (1, 0))
        X_tof = np.expand_dims(X_tof, axis=0)
        X_imu = np.expand_dims(X_imu, axis=0)
        return [X_tof, X_imu]
 
    def inference(self, data):
        # Run inference on the input data - [X_test_tof, X_test_imu]

        predictions = self.model.predict(data)
        y_pred = np.argmax(predictions, axis=1)
        confidence = np.max(predictions, axis=1)
        # Filter out predictions with low confidence
        y_pred[confidence < 0.8] = 0
        return y_pred


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

    first = 1
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
    num_imu_readings = len(imu_data)  # Assuming all IMU lists have the same length
    num_tof_readings = len(tof_data)
    #print(num_imu_readings)
    #print(num_tof_readings)

    # Handle the case when TOF readings already match or exceed IMU readings
    if num_imu_readings <= num_tof_readings:
        return tof_data
    
    interpolated_tof = []
    interpolated_tof.append(tof_data[0])
    for _ in range(num_imu_readings - 1) :
        interpolated_tof.append(tof_data[-1])
    
    '''
    if len(tof_data) == 1:
        
    else:
        for tof_reading in tof_data:
            # Interpolating each depth map in the TOF reading
            x = np.arange(0, 8)
            f = interp1d(x, tof_reading, kind='linear')
            xnew = np.linspace(0, 7, num_imu_readings)
            interpolated_tof.append(f(xnew))
    '''

    return np.array(interpolated_tof).tolist()


def process_data(arduino_right, arduino_left, arduino_right_lock, arduino_left_lock, esp_right, esp_left, esp_right_lock, esp_left_lock):
    global running_window
    tof_data_left = []
    imu_data_left = []
    tof_data_right = []
    imu_data_right = []
    inference_tof_data_left = []
    inference_imu_data_left = []
    inference_tof_data_right = []
    inference_imu_data_right = []
    flush = 3
    model = Model(model_file)
 
    while True:

        #time.sleep(0.01)

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
            left_tof_padded = pad_tof_data(tof_data_left, imu_data_left)
            inference_tof_data_left.extend(left_tof_padded)
            inference_imu_data_left.extend(imu_data_left)
            tof_data_left = []
            imu_data_left = []

        if len(tof_data_right) != 0 and len(imu_data_right) != 0:
            right_tof_padded = pad_tof_data(tof_data_right, imu_data_right)
            inference_tof_data_right.extend(right_tof_padded)
            inference_imu_data_right.extend(imu_data_right)
            tof_data_right = []
            imu_data_right = []

        if len(inference_tof_data_left) >= running_window:
            # Extract the data from the buffer
            X_tof = np.array(inference_tof_data_left[:running_window])
            X_imu = np.array(inference_imu_data_left[:running_window])
            for _ in range(flush) :
                inference_tof_data_left.pop(0)
            for _ in range(flush) :
                inference_imu_data_left.pop(0)
            X = model.format_data(X_tof, X_imu)
            y = model.inference(X)[0]
            if y != 0:
                print(f"Gesture left : {y}")
                inference_tof_data_left = []
                inference_imu_data_left = []
            
                
        if len(inference_tof_data_right) >= running_window:
            # Extract the data from the buffer
            X_tof = np.array(inference_tof_data_right[:running_window])
            X_imu = np.array(inference_imu_data_right[:running_window])
            for _ in range(flush) :
                inference_tof_data_right.pop(0)
            for _ in range(flush) :
                inference_imu_data_right.pop(0)
            X = model.format_data(X_tof, X_imu)
            y = model.inference(X)[0]
            if y != 0:
                print(f"Gesture right : {y}")
                inference_tof_data_right = []
                inference_imu_data_right = []


def main():

    processes = []

    data_arduino = multiprocessing.Queue()
    data_esp = multiprocessing.Queue()
    esp_right = multiprocessing.Queue()
    esp_left = multiprocessing.Queue()
    arduino_right = multiprocessing.Queue()
    arduino_left = multiprocessing.Queue()

    esp_lock = multiprocessing.Lock()
    arduino_lock = multiprocessing.Lock()
    esp_right_lock = multiprocessing.Lock()
    esp_left_lock = multiprocessing.Lock()
    arduino_right_lock = multiprocessing.Lock()
    arduino_left_lock = multiprocessing.Lock()

    serial_port_arduino = serial.Serial((arduino_com), 9600, timeout=1)
    serial_port_esp = serial.Serial((esp_com), 115200, timeout=1)

    # Create processes for each micro function
    processes.append(multiprocessing.Process(target=arduino_read_from_port, args=(serial_port_arduino, data_arduino, arduino_lock)))
    processes.append(multiprocessing.Process(target=esp_read_from_port, args=(serial_port_esp, data_esp, esp_lock)))
    processes.append(multiprocessing.Process(target=process_esp_raw_data, args=(data_esp, esp_lock, esp_right, esp_left, esp_right_lock, esp_left_lock)))
    processes.append(multiprocessing.Process(target=process_arduino_raw_data, args=(data_arduino, arduino_lock, arduino_right, arduino_left, arduino_right_lock, arduino_left_lock)))
    processes.append(multiprocessing.Process(target=process_data, args=(arduino_right, arduino_left, arduino_right_lock, arduino_left_lock, esp_right, esp_left, esp_right_lock, esp_left_lock)))

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
