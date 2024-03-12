import matplotlib.pyplot as plt
import numpy as np
import imageio.v2 as imageio
import json

# Open the JSON file for reading
with open('ally_data.json', 'r') as file:
    # Parse the JSON data
    entries = json.load(file)


# Loop through each entry in your dataset
for j,data in enumerate(entries):
    # Temporary lists for the current entry
    depth_maps_left = []
    depth_maps_right = []
    
    # Extract depth maps from the "left" section of the current entry
    for entry in data["left"]["TOF"]:
        depth_maps_left.append(entry["depth_map"])
    
    # Extract depth maps from the "right" section of the current entry
    for entry in data["right"]["TOF"]:
        depth_maps_right.append(entry["depth_map"])
    
    combined_depth_maps = []

    for left_map, right_map in zip(depth_maps_left, depth_maps_right):
        # Reshape both maps to 8x8
        left_map_reshaped = np.reshape(left_map, (8, 8))
        right_map_reshaped = np.reshape(right_map, (8, 8))
        left_rotated_data = np.rot90(left_map_reshaped)
        left_flipped_data = np.flipud(left_rotated_data)
        right_rotated_data = np.rot90(right_map_reshaped)
        right_flipped_data = np.flipud(right_rotated_data)
    
        # Concatenate them side by side to form an 8x16 array
        combined_map = np.concatenate((left_rotated_data, right_rotated_data), axis=1)
        
        # Add the combined map to the list
        combined_depth_maps.append(combined_map)
    

    filenames = []  # List to hold filenames of all frames

    # Assuming `data_set` is a list of 8x8 matrices, each representing a frame
    for i, data in enumerate(combined_depth_maps):
        plt.figure(figsize=(10, 5))

        # Left hand
        plt.subplot(1, 2, 1) 
        plt.imshow(data[:, 0:8], cmap='viridis')
        plt.axis('off')
        plt.title('Left')

        # Right hand
        plt.subplot(1, 2, 2)
        plt.imshow(data[:,8:16], cmap='viridis')
        plt.axis('off')
        plt.title('Right')

        # Display the plot on the screen
        # plt.show() 

        # Save the figure and close it
        filename = f'images/frame_{i}.png'
        plt.savefig(filename, bbox_inches='tight', pad_inches=0)
        plt.close()
        filenames.append(filename)

    # Create an animated GIF
    animation = f'animations/animation_{j}.gif'
    with imageio.get_writer(animation, mode='I') as writer:
        for filename in filenames:
            image = imageio.imread(filename)
            writer.append_data(image)

