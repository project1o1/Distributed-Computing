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

def main():
    input("Press enter to start")
    commander = Commander("127.0.0.1", PORT)

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
    y = dataset.iloc[:, 1].values

    commander.send_model(model)
    commander.send_data(X, y)

    # print(f"[INFO] Model and data sent to server")

if __name__ == "__main__":
    main()
