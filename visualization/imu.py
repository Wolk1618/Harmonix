import matplotlib.pyplot as plt
import numpy as np
import imageio.v2 as imageio
import json
from matplotlib.lines import Line2D

# Open the JSON file for reading
with open('ally.json', 'r') as file:
    # Parse the JSON data
    data = json.load(file)

def transform_entry_imu_data(entry_imu_data):
    transformed_data = {'accel_x': [], 'accel_y': [], 'accel_z': [], 'gyro_x': [], 'gyro_y': [], 'gyro_z': []}
    for imu_entry in entry_imu_data:
        for key in transformed_data.keys():
            transformed_data[key].append(imu_entry[key])
    return transformed_data

# Define a function to add a single entry's IMU data to the plots
def add_imu_data_to_plot(entry_imu_data_left, entry_imu_data_right, axes, label):

    # Transform IMU data from list of dicts to dict of lists
    imu_data_left = transform_entry_imu_data(entry_imu_data_left)
    imu_data_right = transform_entry_imu_data(entry_imu_data_right)
    
    # Loop over each IMU variable and plot the data for both left and right
    for i, variable in enumerate(imu_variables):
        # Calculate subplot indices for a 3x4 layout
        row = (i * 2) // 4  # Determines row by variable index
        col_left = (i * 2) % 4  # Left column for current variable
        col_right = col_left + 1  # Right column is next to left
        
        # Plot left data
        axes[row, col_left].plot(imu_data_left[variable], label=f'Left {label + 1}', color=colors[label])
        # Plot right data
        axes[row, col_right].plot(imu_data_right[variable], label=f'Right {label + 1}', color=colors[label])


# Initial setup for plotting
imu_variables = ['accel_x', 'gyro_x', 'accel_y', 'gyro_y', 'accel_z', 'gyro_z']
colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
fig, axes = plt.subplots(nrows=3, ncols=4, figsize=(10,8))  # Adjust for a 3x4 layout

for i, variable in enumerate(imu_variables):
    # Determine the subplot index for "left" and "right"
    subplot_idx = i * 2  # Each variable occupies two columns: one for left, one for right
    row = subplot_idx // 4  # Calculate row index
    col = subplot_idx % 4  # Calculate column index for "left"

    # Set titles and labels for "left"
    axes[row, col].set_title(f'Left {variable}')
    axes[row, col].set_xlabel('Sample Index')
    axes[row, col].set_ylabel(variable)
    
    # Assuming there's a next column for "right"; directly increment col index for "right"
    axes[row, col + 1].set_title(f'Right {variable}')
    axes[row, col + 1].set_xlabel('Sample Index')
    axes[row, col + 1].set_ylabel(variable)

# Process and plot IMU data for each entry
for entry in data:
    add_imu_data_to_plot(entry["left"]["IMU"], entry["right"]["IMU"], axes, entry["label"])

# Adjust layout, add legends, and show plot
plt.tight_layout(rect=[0, 0, 1, 0.9])

# Create custom legend handles
legend_handles = [
    Line2D([0], [0], color=colors[0], lw=4, label='Nothing'),
    Line2D([0], [0], color=colors[1], lw=4, label='Volume Up'),
    Line2D([0], [0], color=colors[2], lw=4, label='Volume Down'),
    Line2D([0], [0], color=colors[3], lw=4, label='Filter Up'),
    Line2D([0], [0], color=colors[4], lw=4, label='Filter Down'),
    Line2D([0], [0], color=colors[5], lw=4, label='Loop'),
]

# Add the custom legend to the first subplot as an example
# You can add it to other subplots as needed
fig.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 1), ncol=2)
plt.show()
