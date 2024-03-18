import serial
import threading
import numpy as np

from keras.models import load_model

arduino_com = '/dev/ttyACM0'
esp_com = '/dev/ttyUSB0'
model_file = "Harmonix_v1.h5"
running_window = 18  # Duration of the running window
data_arduino = []
data_esp = []

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

data_left_for_inference = {
    'TOF': [],
    'IMU': []
}

data_right_for_inference = {
    'TOF': [],
    'IMU': []
}

esp_lock = threading.Lock()
arduino_lock = threading.Lock()
raw_data_lock = threading.Lock()

class Model:
    def __init__(self, model_path):
        self.model = load_model(model_path)
 
    def inference(self, data):
        # Run inference on the input data - [X_test_tof, X_test_imu]
        predictions = self.model.predict(data)
        y_pred = np.argmax(predictions, axis=1)
        confidence = np.max(predictions, axis=1)
        # Filter out predictions with low confidence
        y_pred[confidence < 0.8] = 0
 
        return y_pred
    

model = Model(model_file)

# Function to read from serial port and write to a JSON file
def arduino_read_from_port(serial_port):
    global data_arduino

    serial_port.flushInput()

    while True:
        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()
            with arduino_lock:
                data_arduino.append(data)
            
    
# Function to read from serial port and write to a JSON file
def esp_read_from_port(serial_port):
    global data_esp
    
    serial_port.flushInput()

    while True:
        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()
            if data[0] != 'A' and data[0] != 'B' :
                data = serial_port.readline().decode('utf-8').rstrip()
            
            with esp_lock:
                data_esp.append(data)


def pre_process_data_esp():
    global data_esp
    global raw_data

    while True:

        data_bite = None
        with esp_lock:
            if data_esp:
                data_bite = data_esp.pop(0)

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
                with raw_data_lock:
                    raw_data[target]['TOF'].append({
                        "depth_map": array,
                    })


def pre_process_data_arduino():
    global data_arduino
    global raw_data

    while True:
            
        data_bite = None
        with arduino_lock:
            if data_arduino:
                data_bite = data_arduino.pop(0)

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

            with raw_data_lock:
                raw_data[target]['IMU'].append({
                    "accel_x": accel_x,
                    "accel_y": accel_y,
                    "accel_z": accel_z,
                    "gyro_x": gyro_x,
                    "gyro_y": gyro_y,
                    "gyro_z": gyro_z,
                })


def process_data():
    global raw_data

    while True:
        with raw_data_lock:
            #TODO Send the data to the processing function
            print("Hey")
            

def make_prediction_with_running_window():
    global raw_data

    while True:
        with raw_data_lock:
            if len(raw_data['A']['TOF']) >= running_window and len(raw_data['A']['IMU']) >= running_window:
                # Prepare data for inference
                X_test_tof = np.array(raw_data['A']['TOF'][-running_window:])
                X_test_imu = np.array(raw_data['A']['IMU'][-running_window:])
                X_test = [X_test_tof, X_test_imu]
                X_test = np.array(X_test)
                X_test = X_test.reshape(-1, 8, 8, 1)
                y_pred = model.inference(X_test)
                print(y_pred)

                # Remove the oldest data from the buffer
                raw_data['A']['TOF'] = raw_data['A']['TOF'][-running_window:]
                raw_data['A']['IMU'] = raw_data['A']['IMU'][-running_window:]

def main():

    serial_port_arduino = serial.Serial((arduino_com), 9600, timeout=1)
    serial_port_esp = serial.Serial((esp_com), 115200, timeout=1)

    # Create threads for each micro function
    thread_arduino = threading.Thread(target=arduino_read_from_port, args=(serial_port_arduino, ))
    thread_esp = threading.Thread(target=esp_read_from_port, args=(serial_port_esp, ))
    thread_pre_process_esp = threading.Thread(target=pre_process_data_esp)
    thread_pre_process_arduino = threading.Thread(target=pre_process_data_arduino)
    thread_process = threading.Thread(target=process_data)

    print("\nHarmonix started !\n")
    
    thread_arduino.start()
    thread_esp.start()
    thread_pre_process_esp.start()
    thread_pre_process_arduino.start()
    thread_process.start()

    while True:
        user_input = input("Press Q to quit: ")
        if user_input.lower() == "q":
            break

    thread_arduino.join()
    thread_esp.join()
    thread_pre_process_esp.join()
    thread_pre_process_arduino.join()
    thread_process.join()


if __name__ == "__main__":
    main()
