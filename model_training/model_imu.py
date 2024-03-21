import json
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, concatenate
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.layers import Dense, Dropout, Activation, BatchNormalization
from tensorflow.keras.regularizers import l2
 
 
 
def load_json_data_and_labels(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
 
    labels = []
    sensor_data = []
    for entry in data:
        labels.append(entry['label'])  # Extract the relevant label
        sensor_data.append(entry)  # Extract the relevant sensor data
 
    return sensor_data, labels
 
def extract_sensor_data(data, hand):
    tof_data = []
    imu_data = []
 
    for entry in data:
        tof_entry = []
        imu_entry = []
 
        for sensor in entry[hand]['TOF']:
            if len(sensor['depth_map']) == 64:   # Only process the depth maps with the correct length
                tof_entry.append(sensor['depth_map'])
 
        for sensor in entry[hand]['IMU']:
            imu_entry.append([sensor['accel_x'], sensor['accel_y'], sensor['accel_z'], sensor['gyro_x'], sensor['gyro_y'], sensor['gyro_z']])
 
        if tof_entry:
            tof_data.append(tof_entry)
            imu_data.append(imu_entry)
 
    arr_tof = np.array(tof_data, dtype = 'object')
    arr_imu = np.array(imu_data, dtype = 'object')
    return arr_tof, arr_imu
 
def preprocess_tof_data(tof_data, new_shape):
    # Find the minimum length of depth maps among all entries
    min_depth_maps_len = min(len(entry) for entry in tof_data)
 
    num_of_samples = len(tof_data)
    tof_data_reshaped = np.zeros((num_of_samples, min_depth_maps_len, new_shape[0], new_shape[1]))
 
    for i, entry in enumerate(tof_data):
        for j in range(min_depth_maps_len):  # Only process up to the minimum length
            depth_map = entry[j]
            reshaped_depth_map = np.reshape(depth_map, (new_shape[0], new_shape[1]))
            tof_data_reshaped[i, j, :, :] = reshaped_depth_map
 
    # Transpose the axes to get the desired shape (10, 15, 8, 8)
    # tof_data_reshaped = np.transpose(tof_data_reshaped, (0, 2, 3, 1))
 
    return tof_data_reshaped
 
 
 
def preprocess_imu_data(imu_data):
    num_of_samples = len(imu_data)
    num_of_features = 6  # We have 6 features: accel_x, accel_y, accel_z, gyro_x, gyro_y, and gyro_z
    shortest_length = min(len(lst) for lst in imu_data)
    imu_data_reshaped = np.zeros((num_of_samples, num_of_features, shortest_length))
 
    for i, entry in enumerate(imu_data):
        for j, sensor in enumerate(entry):
            if j < shortest_length:
                imu_data_reshaped[i, 0, j] = sensor[0]
                imu_data_reshaped[i, 1, j] = sensor[1]
                imu_data_reshaped[i, 2, j] = sensor[2]
                imu_data_reshaped[i, 3, j] = sensor[3]
                imu_data_reshaped[i, 4, j] = sensor[4]
                imu_data_reshaped[i, 5, j] = sensor[5]
 
    # Transpose the axes to get the desired shape (10, 6, 15)
    imu_data_reshaped = np.transpose(imu_data_reshaped, (0, 2, 1))
 
    return imu_data_reshaped
 
 
def pad_tof_data(tof_data, imu_data):
    padded_tof_data = []
    for i in range(len(tof_data)):
        # Find the number of frames to pad
        num_frames_to_pad = len(imu_data[i]) - len(tof_data[i])
 
        # Interpolate the depth maps
        interpolated_depth_maps = []
        for j in range(len(tof_data[i][0])):
            depth_map = tof_data[i][:, j]
            time = np.linspace(0, 1, len(depth_map))
            interpolator = interp1d(time, depth_map, kind='linear', axis=0, fill_value='extrapolate')
            new_time = np.linspace(0, 1, len(imu_data[i]))
            interpolated_depth_map = interpolator(new_time)
            interpolated_depth_maps.append(interpolated_depth_map)
 
        interpolated_depth_maps = np.array(interpolated_depth_maps)
        interpolated_depth_maps = np.transpose(interpolated_depth_maps, (1, 0, 2))
        padded_tof_data.append(interpolated_depth_maps)
 
    return np.array(padded_tof_data)
 
 
def return_preprocessed_data(data):
 
    # Extract the data for each hand
    left_tof_data, left_imu_data = extract_sensor_data(data, 'left')
    right_tof_data, right_imu_data = extract_sensor_data(data, 'right')
 
    # Preprocess IMU data
    left_imu = preprocess_imu_data(left_imu_data)
    right_imu = preprocess_imu_data(right_imu_data)
 
    # Preprocess TOF data
    left_tof = preprocess_tof_data(left_tof_data, (8, 8))
    right_tof = preprocess_tof_data(right_tof_data, (8, 8))
 
    # Pad the TOF data
    left_tof_padded = pad_tof_data(left_tof, left_imu)
    right_tof_padded = pad_tof_data(right_tof, right_imu)
 
    # Reshape the  data if needed
    left_tof_padded = np.transpose(left_tof_padded, (0, 2, 3, 1))
    right_tof_padded = np.transpose(right_tof_padded, (0, 2, 3, 1))
 
    # Reshape the IMU data if needed
    left_imu = np.transpose(left_imu, (0, 2, 1))
    right_imu = np.transpose(right_imu, (0, 2, 1))
 
 
    return left_tof_padded, right_tof_padded, left_imu, right_imu
 
def split_data_by_label(left_tof, right_tof, left_imu, right_imu, labels, test_size=0.25, random_state=42):
 
    # Split the data separately for each label
    train_data_list = []
    test_data_list = []
 
    for label in range(6):
        # Get the indices of the samples with the current label
        label_indices = np.where(labels == label)[0]
 
        # Split the samples with the current label into training and test sets
        train_indices, test_indices = train_test_split(label_indices, test_size=test_size, random_state=random_state)
 
        # Use the indices to split the sensor data and labels
        train_data_list.append((left_tof[train_indices], right_tof[train_indices], left_imu[train_indices], right_imu[train_indices], label * np.ones(len(train_indices))))
        test_data_list.append((left_tof[test_indices], right_tof[test_indices], left_imu[test_indices], right_imu[test_indices], label * np.ones(len(test_indices))))
 
    # Concatenate the data for all labels
    train_data = tuple(map(np.concatenate, zip(*train_data_list)))
    test_data = tuple(map(np.concatenate, zip(*test_data_list)))
 
    # Convert the labels to one-hot encoding
    train_data = (*train_data[:-1], to_categorical(train_data[-1], num_classes=6))
    test_data = (*test_data[:-1], to_categorical(test_data[-1], num_classes=6))
 
    return train_data, test_data
 
def plot_confusion_matrix(y_true, y_pred):
    # Compute the confusion matrix
    conf_mat = confusion_matrix(y_true, y_pred)
 
    # Plot the confusion matrix
    sns.heatmap(conf_mat, annot=True, fmt='d', cmap='Blues')
    plt.xlabel('Predicted label')
    plt.ylabel('True label')
    plt.show()
 
 
def plot_history(history, metric='loss'):
    if metric == 'loss':
        plt.figure(figsize=(10, 6))
        plt.plot(history.history['loss'], label='Training Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.show()
    elif metric == 'accuracy':
        plt.figure(figsize=(10, 6))
        plt.plot(history.history['accuracy'], label='Training Accuracy')
        plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
        plt.title('Model Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.show()
    else:
        raise ValueError("Invalid metric. Must be either 'loss' or 'accuracy'.")
 
 
 
def main():
    ally_file_path = 'data_collected/ally.json'
    thomas_file_path = 'data_collected/thomas.json'
    ana_file_path = 'data_collected/ana.json'
    seb_file_path = 'data_collected/seb.json'
    data1, labels1 = load_json_data_and_labels(ally_file_path)
    data2, labels2 = load_json_data_and_labels(thomas_file_path)
    data3, labels3 = load_json_data_and_labels(ana_file_path)
    data4, labels4 = load_json_data_and_labels(seb_file_path)
 
    data = data1 + data2 + data3 + data4
    labels = np.array(labels1 + labels2 + labels3 + labels4)
 
    # Extract and preprocess the data for each hand
    left_tof, right_tof, left_imu, right_imu = return_preprocessed_data(data)
 
    #print(left_tof.shape,left_imu.shape)
    #print(left_imu.shape,right_imu.shape)
 
 
    # Split the data
    train_data, test_data = split_data_by_label(left_tof, right_tof, left_imu, right_imu, labels)
 
    # Unpack the training and test data
    X_train_left_tof, X_train_right_tof, X_train_left_imu, X_train_right_imu, y_train = train_data
    X_test_left_tof, X_test_right_tof, X_test_left_imu, X_test_right_imu, y_test = test_data
 
    # Concatenate IMU data
    X_train_imu = np.concatenate((X_train_left_imu, X_train_right_imu), axis=0)
    X_test_imu = np.concatenate((X_test_left_imu, X_test_right_imu), axis=0)
 
    # Concatenate labels
    y_train = np.concatenate((y_train, y_train), axis = 0)
    y_test = np.concatenate((y_test, y_test), axis = 0)
 
 
    # --------- Data augmentation setting ---------
 
    # You can modify the data_augmentation variable below to add your
    # data augmentation pipeline.
    # By default we do not apply any augmentation (RandomZoom(0) is equivalent
    # to not performing any augmentation)
    '''
    data_augmentation = keras.Sequential(
        [
            preprocessing.RandomZoom(0)
        ]
    )
    model.add(data_augmentation)
    '''
 
 
# --------- Model definition ---------
 
    # We will use glorot_uniform as a initialization by default
    initialization = 'glorot_uniform'
    num_time_steps = X_train_left_tof.shape[3]
 
    # # Input for the TOF features (8x8 input features)
    # input1 = Input(shape=(8, 8, num_time_steps))
    # conv1 = Conv2D(32, kernel_size=3, activation='relu', padding='same', kernel_initializer=initialization, kernel_regularizer=l2(0.01))(input1)
    # dropout1 = Dropout(0.5)(conv1)
    # pool1 = MaxPooling2D(pool_size=2, strides=(2, 2), padding='same')(dropout1)
    # flat1 = Flatten()(pool1)
    # dense1 = Dense(32, kernel_initializer=initialization, activation='relu')(flat1)
 
    # Input for the first IMU (6 input features)
    input3 = Input(shape=(6, num_time_steps))
    flat3 = Flatten()(input3)
    dense3 = Dense(32, kernel_initializer=initialization, kernel_regularizer=l2(0.01), activation='relu')(flat3)
 
    # Combined linear layer for merging the outputs
    dense_combined = Dense(256, kernel_initializer=initialization, activation='relu')(dense3)
 
    # Additional linear layers
    dense5 = Dense(128, kernel_initializer=initialization, activation='relu')(dense_combined)
    dense6 = Dense(64, kernel_initializer=initialization, activation='relu')(dense5)
    dense7 = Dense(32, kernel_initializer=initialization, activation='relu')(dense6)
 
    # Output layer
    output = Dense(6, kernel_initializer=initialization, activation='softmax')(dense7)
 
    # --------- Model creation and definition ---------
    # Use early stopping
    es = EarlyStopping(monitor='val_accuracy', patience = 20, verbose = 0)
 
    # Create the model
    model = Model(inputs=[input3], outputs=output)
 
    # By default use Adam with lr=3e-4. Change it to SGD when asked to
    opt = Adam(lr=3e-4)
    model.compile(loss='categorical_crossentropy',
                  optimizer=opt,
                  metrics=['accuracy'])
 
    # Display the model summary
    model.summary()
 
    # --------- Training model ---------
 
    # Use 40 epochs as default value to plot your curves
    history = model.fit([X_train_imu], y_train, epochs=200, validation_data=([X_test_imu], y_test), callbacks=[es])
    model.save('model_imu.h5')
    # Plot the training and validation curves
    plot_history(history, metric='accuracy')
    plot_history(history, metric='loss')
 
    # Print the training and validation accuracy
    train_accuracy = history.history['accuracy'][-1]
    val_accuracy = history.history['val_accuracy'][-1]
    print(f'Training Accuracy: {train_accuracy:.4f}')
    print(f'Validation Accuracy: {val_accuracy:.4f}')
 
    # Evaluate the model on the test data
    predictions = model.predict([X_test_imu])
    y_pred = np.argmax(predictions, axis=1)
    y_test = np.argmax(y_test, axis=1)
    confidence = np.max(predictions, axis=1)
 
    # y_pred[confidence < 0.8] = 0
 
    plot_confusion_matrix(y_test, y_pred)
 
    # Plot a histogram of how confident the model is on each prediction
 
    plt.figure(figsize=(8, 6))
    plt.hist(confidence, bins=10, edgecolor='black')
    plt.title('Distribution of Model Confidence')
    plt.xlabel('Confidence')
    plt.ylabel('Frequency')
    plt.grid(axis='y', alpha=0.75)
    plt.show()
 
 
 
if __name__ == '__main__':
    main()
 