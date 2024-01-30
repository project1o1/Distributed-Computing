import nanoid
import socket
from constants import ACKNOWLEDGEMENT_SIZE, HEADER_SIZE, DATA_SIZE_PER_PACKET
import time
import json
import numpy as np
import tensorflow as tf
import base64

class Client:
    def __init__(self, IP, port):
        self.IP = IP
        self.port = port
        self.ID = nanoid.generate(size=10)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def wait_for_ack(self, expected_ack="ACK"):
        try:
            ack = self.socket.recv(ACKNOWLEDGEMENT_SIZE)
            return ack.decode('utf-8').strip() == expected_ack
        except socket.error as e:
            print(f"[ERROR] Failed to receive acknowledgment: {e}")
            return False

    def send_ack(self, message="ACK"):
        try:
            # print(f"[INFO] Sending acknowledgment: {message}")
            self.socket.send(message.encode('utf-8').ljust(ACKNOWLEDGEMENT_SIZE))
        except socket.error as e:
            print(f"[ERROR] Failed to send acknowledgment: {e}")
            return False
        return True

    def send_message(self, message, max_retries=3, retry_interval=1):
        try:
            # Convert message to bytes using JSON serialization
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')

            # Send the size of the message
            size = len(message_bytes)
            size_data = str(size).encode('utf-8').ljust(HEADER_SIZE)
            # print(f"[INFO] Sending message of size: {size}")
            self.socket.send(size_data)
            # print(f"[INFO] Message size sent successfully. Waiting for acknowledgment...")

            # Receive acknowledgment for the size
            # if not self.wait_for_ack():
            #     print("[ERROR] Failed to send message size acknowledgment")
            #     return
            # print(f"[INFO] Message size acknowledgment received. Sending message...")
            self.socket.sendall(message_bytes)
            # Send the message in chunks with retries
            # chunk_size = DATA_SIZE_PER_PACKET
            # remaining_size = size
            # for i in range(0, size, chunk_size):
            #     if remaining_size < chunk_size:
            #         chunk_size = remaining_size
            #     chunk = message_bytes[i:i + chunk_size]
            #     remaining_size -= chunk_size
            #     self.socket.send(chunk)

                # Receive acknowledgment for the chunk
                # if not self.wait_for_ack():
                #     print("[ERROR] Failed to send message chunk acknowledgment. Retrying...")
                #     # Retry sending the chunk
                #     for retry_count in range(max_retries):
                #         time.sleep(retry_interval)
                #         self.socket.send(chunk)
                #         if self.wait_for_ack():
                #             break
                #     else:
                #         print("[ERROR] Maximum retries reached. Failed to send message chunk.")
                #         return

            # print(f"[INFO] Message sent successfully.")

        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")
    
    def receive_message(self):
        try:
            size_data = self.socket.recv(HEADER_SIZE)
            if not size_data:
                print("[ERROR] Failed to receive message size data.")
                return None

            size = int(size_data.strip().decode('utf-8'))

            # self.send_ack()  # Send acknowledgment for the message size

            # chunks = []
            # remaining_size = size
            # # count = 0
            # while remaining_size > 0:
            #     chunk = self.socket.recv(min(DATA_SIZE_PER_PACKET, remaining_size))
            #     # count += 1
            #     # print(f"[INFO] Received chunk {count}")
            #     if not chunk:
            #         print("[ERROR] Failed to receive message chunk.")
            #         return None

            #     chunks.append(chunk)
            #     remaining_size -= len(chunk)

                # self.send_ack()  # Send acknowledgment for each chunk

            # message_bytes = b''.join(chunks)
            message_bytes = b''
            remaining_size = size
            while remaining_size > 0:
                chunk = self.socket.recv(min(DATA_SIZE_PER_PACKET, remaining_size))
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
            return None
        
    def send_model(self, model):
        model_params = model.get_weights()
        model_params_json = json.dumps([param.tolist() for param in model_params])
        model_architecture = model.to_json()
        message = {
            "model_architecture": model_architecture,
            "model_params": model_params_json
        }
        self.send_message(message)
        print(f"[INFO] Model sent to server")

    def send_data(self, X, y):
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
            "y_shape": y_shape
        }
        self.send_message(message)
        print(f"[INFO] Data sent to server")

    def receive_model(self):
        message = self.receive_message()
        model_architecture = message["model_architecture"]
        model_params_json = message["model_params"]
        model_params = [np.array(param) for param in json.loads(model_params_json)]
        model = tf.keras.models.model_from_json(model_architecture)
        model.set_weights(model_params)
        print(f"[INFO] Model received from server")
        return model