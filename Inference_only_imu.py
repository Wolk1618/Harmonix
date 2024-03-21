import serial
import multiprocessing
import time
import numpy as np
import socket

from tensorflow.keras.models import load_model
#from scipy.interpolate import interp1d

arduino_com = '/dev/ttyACM3'
running_window = 18  # Size of the running window
host = '172.20.112.1'  # The server's hostname or IP address
port = 12345  # The port used by the server
model_file = 'model_imu.h5'
vol_current_value = {
    1: 0,
    2: 0
}
fader_current_value = {
    1: 63,
    2: 63
}
max_value = 127
loopBool = False

class Model:
    def __init__(self, model_path):
        self.model = load_model(model_path)

    def format_data(self, X_imu):
        X_imu = np.reshape(X_imu, (18, 6))
        X_imu = np.transpose(X_imu, (1, 0))
        X_imu = np.expand_dims(X_imu, axis=0)
        return [X_imu]
 
    def inference(self, data):
        # Run inference on the input data - [X_test_imu]
        predictions = self.model.predict(data)
        y_pred = np.argmax(predictions, axis=1)
        confidence = np.max(predictions, axis=1)
        # Filter out predictions with low confidence
        y_pred[confidence < 0.8] = 0
        return y_pred
    
def send_data(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(data.encode())
        print(f"Sent data: {data}")


# Function to read from serial port and write to a JSON file
def arduino_read_from_port(serial_port, data_arduino, arduino_lock):
    serial_port.flushInput()

    while True:

        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()

            with arduino_lock:
                data_arduino.put(data)


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



def make_inference(arduino_right, arduino_left, arduino_right_lock, arduino_left_lock):
    global running_window
    imu_data_left = []
    imu_data_right = []
    spotted_right = 0
    spotted_left = 0
    flush = 1
    model = Model(model_file)
 
    while True:

        #time.sleep(0.01)

        with arduino_right_lock:
            while not arduino_right.empty():
                imu_data_right.append(arduino_right.get())

        with arduino_left_lock:
            while not arduino_left.empty():
                imu_data_left.append(arduino_left.get())


        if len(imu_data_left) >= running_window:
            # Extract the data from the buffer
            X_imu = np.array(imu_data_left[:running_window])
            for _ in range(flush) :
                imu_data_left.pop(0)
            X = model.format_data(X_imu)
            y = model.inference(X)[0]
            if y != 0:
                if spotted_left == 0:
                    for _ in range(9) :
                        imu_data_left.pop(0)
                    spotted_left = 1
                else :
                    send_data(str(0) + str(y))
                    spotted_left = 0
                    imu_data_left = []
            
                
        if len(imu_data_right) >= running_window:
            # Extract the data from the buffer
            X_imu = np.array(imu_data_right[:running_window])
            for _ in range(flush) :
                imu_data_right.pop(0)
            X = model.format_data(X_imu)
            y = model.inference(X)[0]
            if y != 0:
                if spotted_right == 0:
                    for _ in range(9) :
                        imu_data_right.pop(0)
                    spotted_right = 1
                else :
                    send_data(str(1) + str(y))
                    spotted_right = 0
                    imu_data_right = []
   


def main():

    processes = []

    data_arduino = multiprocessing.Queue()
    arduino_right = multiprocessing.Queue()
    arduino_left = multiprocessing.Queue()

    arduino_lock = multiprocessing.Lock()
    arduino_right_lock = multiprocessing.Lock()
    arduino_left_lock = multiprocessing.Lock()

    serial_port_arduino = serial.Serial((arduino_com), 9600, timeout=1)

    # Create processes for each micro function
    processes.append(multiprocessing.Process(target=arduino_read_from_port, args=(serial_port_arduino, data_arduino, arduino_lock)))
    processes.append(multiprocessing.Process(target=process_arduino_raw_data, args=(data_arduino, arduino_lock, arduino_right, arduino_left, arduino_right_lock, arduino_left_lock)))
    processes.append(multiprocessing.Process(target=make_inference, args=(arduino_right, arduino_left, arduino_right_lock, arduino_left_lock)))

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
