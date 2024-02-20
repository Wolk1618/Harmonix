import serial
import numpy as np
import matplotlib.pyplot as plt
import time
 
COM_PORT = 'COM9'
BAUD_RATE = 115200
 
# Initialize serial connection
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
 
 # Set up the plot
plt.ion()  # Turn on interactive mode
 
fig, (ax1, ax2) = plt.subplots(1, 2)  # Create two subplots
 
# Initial depth maps
depth_map1 = np.zeros((8, 8))
depth_map2 = np.zeros((8, 8))
 
img2 = ax1.imshow(depth_map1, interpolation='none', aspect='equal', cmap='viridis', vmin=-500, vmax=2000)
img1 = ax2.imshow(depth_map2, interpolation='none', aspect='equal', cmap='viridis', vmin=-500, vmax=2000)
 
def update_plot(data, img):
    """
    Updates the plot with new data.
    """
    rotated_data = np.rot90(data)
    fliped_data = np.flipud(rotated_data)
    img.set_data(fliped_data)
    plt.draw()
    plt.pause(0.01)
 
def read_and_print_sensor_data():
    depth_values1 = []
    depth_values2 = []
    count = 0  # No sensor selected initially
 
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').rstrip()
                if line.startswith('Sensor 1 Depth Map:'):
                    count = 1  # Sensor 1 data incoming
                    depth_values1 = []  # Reset the list for sensor 1
                elif line.startswith('Sensor 2 Depth Map:'):
                    count = 2  # Sensor 2 data incoming
                    depth_values2 = []  # Reset the list for sensor 2
                else:
                    try:
                        values = [int(val) for val in line.split('\t') if val]  # Split on tabs and parse integers
                        if count == 1:
                            depth_values1.extend(values)
                        elif count == 2:
                            depth_values2.extend(values)
                    except ValueError:
                        # Handle the case where conversion to int fails
                        pass
 
                # Check if we have collected enough values for a full depth map
                if count == 1 and len(depth_values1) >= 64:
                    depth_map1 = np.array(depth_values1[:64]).reshape((8, 8))  # Use the first 64 values
                    update_plot(depth_map1, img1)
                    print("Sensor 1 Depth Map:", depth_map1)
                    depth_values1 = depth_values1[64:]  # Remove the used values
                elif count == 2 and len(depth_values2) >= 64:
                    depth_map2 = np.array(depth_values2[:64]).reshape((8, 8))
                    # Update the plot for sensor 2 if needed, or process as required
                    update_plot(depth_map2, img2)
                    print("Sensor 2 Depth Map:", depth_map2)
                    depth_values2 = depth_values2[64:]  # Remove the used values
 
    except KeyboardInterrupt:
        print("Stopped by User")
        ser.close()
        plt.close(fig)
 
 
if __name__ == "__main__":
    read_and_print_sensor_data()