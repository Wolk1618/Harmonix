import numpy as np
from tensorflow.keras.models import load_model

model_file = 'final_model.h5'

class Model:
    def __init__(self, model_path):
        self.model = load_model(model_path)

    def format_data(self, X_tof, X_imu):
        #X_tof = np.reshape(X_tof, (1, 18, 8, 8))
        #X_imu = np.reshape(X_imu, (1, 18, 6))
        #X_tof = np.transpose(X_tof, (0, 2, 3, 1))
        #X_imu = np.transpose(X_imu, (0, 2, 1))
        X_tof = np.reshape(X_tof, (18, 8, 8))
        X_imu = np.reshape(X_imu, (18, 6))
        X_tof = np.transpose(X_tof, (1, 2, 0))
        X_imu = np.transpose(X_imu, (1, 0))
        X_tof = np.expand_dims(X_tof, axis=0)
        X_imu = np.expand_dims(X_imu, axis=0)
        return [X_tof, X_imu]
 
    def inference(self, data):
        # Run inference on the input data - [X_test_tof, X_test_imu]

        predictions = self.model.predict(data)
        y_pred = np.argmax(predictions, axis=1)
        confidence = np.max(predictions, axis=1)
        # Filter out predictions with low confidence
        y_pred[confidence < 0.8] = 0
        return y_pred


def predict_worker(inference_queue, inference_lock, prediction_queue, prediction_lock):
    # Load your model
    model = Model(model_file)

    while True :

        data = None

        with inference_lock:
            if not inference_queue.empty():
                # Get the input data from the queue
                data = inference_queue.get()

        if data is not None:
            hand = data[0]
            # Make predictions
            input_data = model.format_data(data[1], data[2])
            prediction = model.inference(input_data)

            # Send the predictions to the main process using the queue
            with prediction_lock:
                prediction_queue.put([hand, prediction])