import numpy as np
from keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, concatenate, GlobalAveragePooling2D
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Activation, BatchNormalization
import np_utils
from keras.datasets import cifar10
from keras.optimizers import Adam, SGD
from keras import regularizers
from tensorflow.keras.layers.experimental import preprocessing
import matplotlib.pyplot as plt


# --------- Global variables ---------
num_classes = 7
channels_k = 50


# --------- Function definition ---------

def plot_history(history, metric = None):
  # Plots the loss history of training and validation (if existing)
  # and a given metric
  # Be careful because the axis ranges are automatically adapted
  # which may not desirable to compare different runs.
  # Also, in some cases you may want to combine several curves in one
  # figure for easier comparison, which this function does not do.

  if metric != None:
    fig, axes = plt.subplots(2,1)
    axes[0].plot(history.history[metric])
    try:
      axes[0].plot(history.history['val_'+metric])
      axes[0].legend(['Train', 'Val'])
    except:
      pass
    axes[0].set_title('{:s}'.format(metric))
    axes[0].set_ylabel('{:s}'.format(metric))
    axes[0].set_xlabel('Epoch')
    fig.subplots_adjust(hspace=0.5)
    axes[1].plot(history.history['loss'])
    try:
      axes[1].plot(history.history['val_loss'])
      axes[1].legend(['Train', 'Val'])
    except:
      pass
    axes[1].set_title('Model Loss')
    axes[1].set_ylabel('Loss')
    axes[1].set_xlabel('Epoch')
  else:
    plt.plot(history.history['loss'])
    try:
      plt.plot(history.history['val_loss'])
      plt.legend(['Train', 'Val'])
    except:
      pass
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')


# --------- Data preparation ---------

# load the data TODO
'''
(X_train, y_train), (X_test, y_test) = cifar10.load_data()

print('Total number of training samples: {0}'.format(X_train.shape[0]))
print('Total number of validation samples: {0}'.format(X_test.shape[0]))

# TODO Adapt shape to data
# X_train = X_train.reshape(-1,32,32,3)

## Normalization block
norm_layer = preprocessing.Normalization()
norm_layer.adapt(X_train)
X_train_n = norm_layer(X_train)
X_test_n = norm_layer(X_test)

Y_train_class = np_utils.to_categorical(y_train, num_classes)
Y_test_class = np_utils.to_categorical(y_test, num_classes)
'''


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

# Input for the first TOF features (8x8 input features)
input1 = Input(shape=(8, 8, channels_k))
conv1 = Conv2D(32, kernel_size=3, activation='relu', padding='same', kernel_initializer=initialization)(input1)
pool1 = MaxPooling2D(pool_size=2, strides=(2, 2), padding='same')(conv1)
flat1 = Flatten()(pool1)
dense1 = Dense(32, kernel_initializer=initialization, activation='relu')(flat1)

# Input for the second TOF features (8x8 input features)
input2 = Input(shape=(8, 8, channels_k))
conv2 = Conv2D(32, kernel_size=3, activation='relu', padding='same', kernel_initializer=initialization)(input2)
pool2 = MaxPooling2D(pool_size=2, strides=(2, 2), padding='same')(conv2)
flat2 = Flatten()(pool2)
dense2 = Dense(32, kernel_initializer=initialization, activation='relu')(flat2)

# Input for the first IMU (6 input features)
input3 = Input(shape=(6, channels_k))
flat3 = Flatten()(input3)
dense3 = Dense(32, kernel_initializer=initialization, activation='relu')(flat3)

# Input for the first IMU (6 input features)
input4 = Input(shape=(6, channels_k))
flat4 = Flatten()(input4)
dense4 = Dense(32, kernel_initializer=initialization, activation='relu')(flat4)

# Concatenate the outputs from both sets of layers
merged = concatenate([dense1, dense2, dense3, dense4])

# Combined linear layer for merging the outputs
dense_combined = Dense(256, kernel_initializer=initialization, activation='relu')(merged)

# Additional linear layers
dense5 = Dense(128, kernel_initializer=initialization, activation='relu')(dense_combined)
dense6 = Dense(64, kernel_initializer=initialization, activation='relu')(dense5)
dense7 = Dense(32, kernel_initializer=initialization, activation='relu')(dense6)

# Output layer
output = Dense(num_classes, kernel_initializer=initialization, activation='softmax')(dense7) 


# --------- Model creation and definition ---------

# Create the model
model = Model(inputs=[input1, input2, input3, input4], outputs=output)

# By default use Adam with lr=3e-4. Change it to SGD when asked to
opt = Adam(lr=3e-4)
model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])

# Display the model summary
model.summary()


# --------- Training model ---------

# Use 40 epochs as default value to plot your curves
#history = model.fit(X_train_n, Y_train_class, epochs=40, validation_data=(X_test_n, Y_test_class))