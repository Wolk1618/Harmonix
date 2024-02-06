import serial
import numpy as np

COM_PORT = 'COM9' 
BAUD_RATE = 115200

# Initialize serial connection
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

def read_and_print_sensor_data():
    depth_values1 = []
    depth_values2 = []
    count = 1
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').rstrip()
                #print(line)
                if line == '':
                    print(line)
                elif line == 'Sensor 1 Depth Map:':
                    print(line)
                    count = 1
                    if depth_values1:
                        depth_values1 = np.array(depth_values1).reshape((8,8))
                    print(depth_values1)
                    depth_values1 = []
                elif line == 'Sensor 2 Depth Map:':
                    print(line)
                    count = 2
                    if depth_values2:
                        depth_values2 = np.array(depth_values2).reshape((8,8))
                    print(depth_values2)
                    depth_values2 = []
                else:
                    values = [int(val) for val in line.split()]
                    if count == 1:
                        depth_values1.extend(values)
                    else: 
                        depth_values2.extend(values)

    except KeyboardInterrupt:
        print("Stopped by User")
        ser.close()

if __name__ == "__main__":
    read_and_print_sensor_data()