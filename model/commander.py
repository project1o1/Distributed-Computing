from client import Client
from constants import PORT
import time
import base64
import os
import tensorflow as tf
import numpy as np
import pandas as pd
import json

class Commander(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "commander"
        self.socket.connect((self.IP, self.port))
        self.send_message(self.type)
        self.send_message(self.ID)
        print(f"[INFO] Client {self.ID} connected to server")
        self.no_of_frames = 0
                
    def message_server(self, model_architecture, param_dtype, param_dshape, model_params_json, X, y):
        print(f"[INFO] Sending file to server")
        start = time.time()
        message = {
            "model_architecture": model_architecture,
            "model_params": model_params_json,
            "X": base64.b64encode(X).decode('utf-8'),
            "y": base64.b64encode(y).decode('utf-8'),
            "param_dtype": base64.b64encode(param_dtype.encode('utf-8')).decode('utf-8'),
            "param_dshape": base64.b64encode(json.dumps(param_dshape).encode('utf-8')).decode('utf-8'),
        }
        # send file
        self.send_message(message)
        print(f"[INFO] File sent to server")

def main():
    input("Press enter to start")
    commander = Commander("0.0.0.0", PORT)

    # create a model
    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(32, input_shape=(6,), activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    # load data
    dataset = pd.read_csv("./dataset/train.csv")
    
    X = dataset.drop(['PassengerId', 'Name', 'Sex', 'Ticket', 'Cabin', 'Embarked'], axis=1)
    X = np.array(X, dtype=np.float32)
    X = X.tobytes()

    y = dataset.iloc[:, 1].values
    y = np.array(y, dtype=np.float32)
    y = y.tobytes()

    model_params = model.get_weights()

    # Convert NumPy arrays to lists
    model_params_json = json.dumps([param.tolist() for param in model_params])

    param_dtype = model_params[0].dtype.name  # Assuming all parameters have the same dtype
    param_dshape = model_params[0].shape  # Assuming all parameters have the same shape

    model_architecture = model.to_json()

    # send model parameters
    commander.message_server(model_architecture, param_dtype, param_dshape, model_params_json, X, y)

    print(f"[INFO] Model parameters sent to server")

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
