from client import Client
from constants import PORT
import time
import base64
import os
import tensorflow as tf
import numpy as np
import pandas as pd
import json
from sklearn.preprocessing import LabelEncoder

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
    # model = tf.keras.models.Sequential([
    #     tf.keras.layers.Dense(32, input_shape=(8,), activation='relu'),
    #     tf.keras.layers.Dense(64, activation='relu'),
    #     tf.keras.layers.Dense(32, activation='relu'),
    #     tf.keras.layers.Dense(1, activation='sigmoid')
    # ])
    
    # load data
    df = pd.read_csv('./dataset/train.csv')

    # Extract features and target variable
    X = df.drop(['Weight', 'Index'], axis=1).to_numpy().reshape(-1, 1)  # Features
    y = df['Height']  # Target variable

    # Clean and transform string data to numerical values
    # le = LabelEncoder()
    # X['Sex'] = le.fit_transform(X['Sex'])
    # X['Cabin'] = le.fit_transform(X['Cabin'])
    # X['Embarked'] = le.fit_transform(X['Embarked'])
    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(32, input_shape=(X.shape[1],), activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(1)
    ])

    epochs = 3

    commander.send_model(model)
    commander.send_data(X, y, epochs)

    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    print(model.evaluate(X, y))
    model_params = commander.receive_model_params()
    model.set_weights(model_params)
    # model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    print(model.evaluate(X, y))


if __name__ == "__main__":
    main()
