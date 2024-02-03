from client import Client
from constants import PORT
import os
import base64
import time
import tensorflow as tf

blender_path = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
output_format = "PNG"

class Worker(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "worker"
        self.socket.connect((self.IP, self.port))
        
        if not os.path.exists("worker_blend_files"):
            os.mkdir("worker_blend_files")

        self.send_message(self.type)
        self.send_message(self.ID)
        print(f"[INFO] Client {self.ID} connected to server")
        self.start_task_loop()

    def start_message_loop(self):
        while True:
            user_input = input("Enter message to send (or type 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break
            self.send_message(user_input)
    
    def start_task_loop(self):
        while True:
            model = self.receive_model()
            data = self.receive_data()
            X, y, epochs = data

            # print(model.summary())

            for i in range(epochs):
                model_params = self.receive_model_params()
                model.set_weights(model_params)
                with tf.GradientTape() as tape:
                    y_pred = model(X, training=True)
                    loss = tf.keras.losses.binary_crossentropy(y, y_pred)
                # print(f"[INFO] Epoch {i+1}: Loss = {loss}")
                gradients = tape.gradient(loss, model.trainable_variables)
                print(gradients[0].dtype)
                self.send_gradient(gradients)
                model_params = self.receive_model_params()
                model.set_weights(model_params)
                   

if __name__ == "__main__":
    w = Worker("127.0.0.1", PORT)
