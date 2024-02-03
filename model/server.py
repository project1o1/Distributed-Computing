# server.py
import socket
import threading
from constants import ACKNOWLEDGEMENT_SIZE, HEADER_SIZE, PORT, DATA_SIZE_PER_PACKET
import time
from queue import Queue
from threading import Lock
import nanoid
import json
import base64
import os
import tensorflow as tf
from tensorflow.keras.models import model_from_json
import numpy as np

N_CHUNKS = 1

class Server:
    def __init__(self, IP, port):
        self.IP = IP
        self.PORT = port
        self.workers = {}
        self.worker_status = {}
        self.commanders = {}
        self.commander_status = {}

        self.assigned_tasks = {}

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.IP, self.PORT))
        self.message_queue = Queue()

        self.result_queues = Queue()
        self.present_queue = 0

        self.all_messages = {}

        self.result_lengths = {}
        self.result_sent_lengths = {}

        self.models = {}
        self.model_lock = Lock()
        self.model_training = {}

        self.lock = Lock()
        # self.result_lock = Lock()

    def start(self):
        self.server_socket.listen()
        print(f"[INFO] Server listening on {self.IP}:{self.PORT}")
        threading.Thread(target=self.handle_result_queue).start()

        threading.Thread(target=self.order_messages).start()
        # threading.Thread(target=self.worker_health_check).start()
        while True:
            client_socket, client_address = self.server_socket.accept()
            # self.send_ack(client_socket, "CONNECTED")  # Send acknowledgment for connection establishment
            client_type = self.receive_message(client_socket)
            # self.send_ack(client_socket)  # Send acknowledgment for client type receipt

            if client_type == "worker":
                worker_id = self.receive_message(client_socket)
                # self.send_ack(client_socket)
                # self.lock.acquire()
                self.workers[worker_id] = (client_socket, client_address)
                self.worker_status[worker_id] = "idle"
                # self.lock.release()
                print(f"[INFO] Worker {worker_id} connected to server")

                threading.Thread(target=self.handle_worker_send, args=(client_socket, worker_id)).start()
                # threading.Thread(target=self.handle_worker_receive, args=(client_socket, client_address, worker_id)).start()

            elif client_type == "commander":
                threading.Thread(target=self.handle_commander, args=(client_socket, client_address)).start()

    def handle_result_queue(self):
        while True:
            model_ids = list(self.models.keys())
            for model_id in model_ids:
                if self.model_training[model_id] == N_CHUNKS:
                    commander_socket, commander_address = self.commanders[model_id]
                    self.send_model_params(self.models[model_id], commander_socket)

    def handle_worker_send(self, worker_socket, worker_id):
        while True:
            if self.worker_status[worker_id] == "busy":
                continue

            # self.lock.acquire()
            if not self.message_queue.empty():
                message = self.message_queue.get()
                self.worker_status[worker_id] = "busy"

                X, y, epochs = message["message"]["X"], message["message"]["y"], message["message"]["epochs"]
                commander_id = message["commander_id"]

                model = self.models[commander_id]
                self.send_model(model, worker_socket)

                self.send_data(X, y, epochs, worker_socket)

                for i in range(epochs):
                    self.send_model_params(model, worker_socket)
                    gradients = self.receive_gradient(worker_socket)
                    print(gradients[0].dtype)
                    with self.model_lock:
                        model = self.models[commander_id]
                        optimizer = model.optimizer
                        optimizer.apply_gradients(zip(gradients, model.trainable_variables))
                        self.models[commander_id] = model

                    self.send_model_params(model, worker_socket)

                self.model_training[commander_id] += 1
                self.worker_status[worker_id] = "idle"



                # self.handle_worker_receive(worker_socket, worker_id, message["commander_id"], message["message"]["start_frame"], message["message"]["end_frame"])
            # self.lock.release()

    def handle_worker_receive(self, worker_socket, worker_id, commander_id, start_frame, end_frame):
        i = 0
        while i < end_frame - start_frame + 1:
            message = self.receive_message(worker_socket)
            if message is None:
                break
            self.worker_status[worker_id] = "idle"
            message["commander_id"] = commander_id
            # self.result_queues[self.present_queue].put(message)
            # self.present_queue = (self.present_queue + 1) % 2
            with self.lock:
                if self.result_queues[self.present_queue].qsize() > 30:
                    self.present_queue = (self.present_queue + 1) % 2
                self.result_queues[self.present_queue].put(message)            
            # self.result_queue.put(message)
            # print(self.result_queue.qsize())
            i += 1
        

    def handle_commander(self, commander_socket, commander_address):
        commander_id = self.receive_message(commander_socket)
        self.commanders[commander_id] = (commander_socket, commander_address)
        self.commander_status[commander_id] = "idle"
        print(f"[INFO] Commander {commander_id} connected to server")

        while True:
            if not self.commander_status[commander_id]:
                break
            if self.commander_status[commander_id] == "busy":
                continue

            model = self.receive_model(commander_socket)
            model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            self.models[commander_id] = model
            self.model_training[commander_id] = 0
            print(f"[INFO] Model received from commander {commander_id}")
            X, y, epochs = self.receive_data(commander_socket)
            print(f"[INFO] Data received from commander {commander_id}")
            self.commander_status[commander_id] = "busy"

            n_chunks = N_CHUNKS  # len(self.workers)
            chunk_size = int(X.shape[0] / n_chunks)

            for i in range(n_chunks):
                x = X[i * chunk_size: (i + 1) * chunk_size]
                y_ = y[i * chunk_size: (i + 1) * chunk_size]
                message = {
                    "X" : x,
                    "y" : y_,
                    "epochs" : epochs,
                }
                self.add_message_to_queue(message, commander_id, i)


                
                

    def add_message_to_queue(self, message, commander_id, index):
        message_received = {
                "commander_id": commander_id,
                "message": message,
                "timestamp": time.time(),
                "message_id": nanoid.generate(size=10),
                "message_type": "task",
                "chunk_number": index
            }
        self.message_queue.put(message_received)
        # self.all_messages[commander_id].put(message_received)
        print(f"[INFO] Message added to message queue")
        # print(self.all_messages)
        # print(f"[INFO] Message added to message queue")

    def order_messages(self):
        while True:
            # Make a copy of the keys to ensure the loop considers new keys
            commander_ids = list(self.all_messages.keys())
            # print(f"[INFO] Commander IDs: {commander_ids}")
            for commander_id in commander_ids:
                if not self.all_messages[commander_id].empty():
                    # print(f"[INFO] Message queue size for commander {commander_id}: {self.all_messages[commander_id].qsize()}")
                    message = self.all_messages[commander_id].get()
                    self.message_queue.put(message)
                    # print(f"[INFO] Message of commander {commander_id} added to message queue")

    def receive_message(self, connection):
        try:
            size_data = connection.recv(HEADER_SIZE)
            if not size_data:
                print("[ERROR] Failed to receive message size data.")
            #     return None
            # print(f"[INFO] Message size data received successfully. Waiting for message size... {size_data}")
            size = int(size_data.strip().decode('utf-8'))
            # print(f"[INFO] Message size received successfully. Waiting for message... {size}")
            # message_bytes = connection.recv(size)
            message_bytes = b''
            remaining_size = size
            while remaining_size > 0:
                chunk = connection.recv(min(DATA_SIZE_PER_PACKET, remaining_size))
                if not chunk:
                    print("[ERROR] Failed to receive message chunk.")
                    return None
                message_bytes += chunk
                remaining_size -= len(chunk)
            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)  # Decode the JSON message

            return message

        except socket.error as e:
            print(f"[ERROR] Failed to receive message: {e}")
            connection.close()
            return None

    def send_message(self, message, conn, max_retries=3, retry_interval=1):
        try:
            # Convert message to bytes using JSON serialization
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')

            # Send the size of the message
            size = len(message_bytes)
            # print(f"[INFO] Sending message of size: {size}")
            size_data = str(size).encode('utf-8').ljust(HEADER_SIZE)
            # print(f"[INFO] Sending message of size: {len(size_data)}")
            conn.send(size_data)
            conn.sendall(message_bytes)

        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")

    def receive_model(self, conn):
        message = self.receive_message(conn)
        model_architecture = message["model_architecture"]
        model_params_json = message["model_params"]
        model_params_list = json.loads(model_params_json)
        model_params = [np.array(param) for param in model_params_list]
        model = model_from_json(model_architecture)
        model.set_weights(model_params)
        return model
    
    def send_model(self, model, conn):
        model_architecture = model.to_json()
        model_params = model.get_weights()
        model_params_list = [param.tolist() for param in model_params]
        model_params_json = json.dumps(model_params_list)
        message = {
            "model_architecture": model_architecture,
            "model_params": model_params_json
        }
        self.send_message(message, conn)

    def send_model_params(self, model, conn):
        model_params = model.get_weights()
        model_params_json = json.dumps([param.tolist() for param in model_params])
        message = {
            "model_params": model_params_json
        }
        self.send_message(message, conn)
    
    def send_data(self, X, y, epochs, conn):
        X_shape = X.shape
        y_shape = y.shape
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        X = X.tobytes()
        y = y.tobytes()
        message = {
            "X": base64.b64encode(X).decode('utf-8'),
            "X_shape": X_shape,
            "y": base64.b64encode(y).decode('utf-8'),
            "y_shape": y_shape,
            "epochs": epochs
        }
        self.send_message(message, conn)

    def receive_data(self, conn):
        message = self.receive_message(conn)
        X = base64.b64decode(message["X"])
        y = base64.b64decode(message["y"])
        X = np.frombuffer(X, dtype=np.float32)
        y = np.frombuffer(y, dtype=np.float32)
        X_shape = message["X_shape"]
        y_shape = message["y_shape"]
        X = X.reshape(X_shape)
        y = y.reshape(y_shape).reshape((-1,1))
        epochs = message["epochs"]
        return X, y, epochs
    
    def receive_gradient(self, conn):
        message = self.receive_message(conn)
        gradients_json = message["gradients"]
        gradients_list = json.loads(gradients_json)
        gradients = [np.array(gradient) for gradient in gradients_list]
        gradients = [tf.cast(gradient, dtype=tf.float32) for gradient in gradients]
        return gradients

    def send_ack(self, conn, message="ACK"):
        try:
            ack_message = message.encode('utf-8').ljust(ACKNOWLEDGEMENT_SIZE)
            conn.send(ack_message)
        except socket.error as e:
            print(f"[ERROR] Failed to send acknowledgment: {e}")

    def wait_for_ack(self, conn, expected_ack="ACK"):
        try:
            # print(f"[INFO] Waiting for acknowledgment: {expected_ack}")
            ack = conn.recv(ACKNOWLEDGEMENT_SIZE)
            return ack.decode('utf-8').strip() == expected_ack
        except socket.error as e:
            print(f"[ERROR] Failed to receive acknowledgment: {e}")
            return False

s = Server("0.0.0.0", port=PORT)
s.start()
