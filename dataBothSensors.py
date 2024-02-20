import serial
import threading

def read_from_port(serial_port):
    while True:
        if serial_port.in_waiting:
            data = serial_port.readline().decode('utf-8').rstrip()
            print(f"Data from {serial_port.port}: {data}")

def main():
    # Set up COM9 at 1200 baud
    serial_port_com9 = serial.Serial('COM9', 1200, timeout=1)
    # Set up COM12 at 115200 baud
    serial_port_com12 = serial.Serial('COM12', 115200, timeout=1)

    # Create threads for each COM port
    thread_com9 = threading.Thread(target=read_from_port, args=(serial_port_com9,))
    thread_com12 = threading.Thread(target=read_from_port, args=(serial_port_com12,))

    # Start threads
    thread_com9.start()
    thread_com12.start()

    # Join threads to the main thread to keep them alive
    thread_com9.join()
    #thread_com12.join()

if __name__ == "__main__":
    main()
