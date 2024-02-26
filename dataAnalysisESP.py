import serial
import numpy as np
import pyqtgraph as pg
# Import QApplication from QtWidgets instead of QtGui
from PyQt5.QtWidgets import QApplication  # If using PyQt5
# from PySide2.QtWidgets import QApplication  # If using PySide2

COM_PORT = 'COM12'  # Update with your actual COM port
BAUD_RATE = 115200

# Initialize serial connection
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

# PyQtGraph setup
app = QApplication([])  # Use QApplication from QtWidgets
win = pg.GraphicsLayoutWidget(title="Real-time depth maps")
win.resize(1000, 600)
win.show()

p1 = win.addPlot(title="Depth Map Sensor A")
p2 = win.addPlot(title="Depth Map Sensor B")
img1 = pg.ImageItem(border='w')
img2 = pg.ImageItem(border='w')
p1.addItem(img1)
p2.addItem(img2)

# Set color maps
colormap = pg.colormap.get('viridis')  # Use getColormap if this doesn't work
img1.setLookupTable(colormap.getLookupTable())
img2.setLookupTable(colormap.getLookupTable())
img1.setLevels([-100, 4000])
img2.setLevels([-100, 4000])

def update_plot(data, img):
    img.setImage(data)

def process_data_line(data_line):
    clean_data = data_line[1:-2]
    numbers = [int(num) for num in clean_data.split(';') if num]
    matrix = np.array(numbers).reshape((8, 8))
    return matrix

def main():
    looking_for_data = False
    while True:
        QApplication.processEvents()  # Ensure the app remains responsive
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            #if "Ranging frequency 2: 52 Hz" in line:
            #    looking_for_data = True
            looking_for_data = True
            if looking_for_data and line.startswith(('A', 'B')) and line.endswith('Z;'):
                matrix = process_data_line(line)
                if line.startswith('A'):
                    update_plot(matrix, img1)
                elif line.startswith('B'):
                    update_plot(matrix, img2)

if __name__ == "__main__":
    main()
