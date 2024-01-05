import socket
import nanoid
import time
from constants import ACKNOWLEDGEMENT_SIZE, HEADER_SIZE

class Worker:
    def __init__(self, serverIP, port):
        self.serverIP = serverIP
        self.port = port
        self.ID = nanoid.generate(size=10)
        self.type = "worker"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.serverIP, self.port))
        if self.wait_for_ack():
            self.send_message(self.ID)
            if self.wait_for_ack():
                print(f"[INFO] Worker {self.ID} connected to server")
            else:
                print(f"[ERROR] Failed to connect to server")
                exit(1)
        else:
            print(f"[ERROR] Failed to connect to server")
            exit(1)

    def send_message(self, message, max_retries=3, retry_interval=1):
        try:
            # Convert message to bytes
            message_bytes = message.encode('utf-8')

            # Send the size of the message
            size = len(message_bytes)
            size_data = str(size).encode('utf-8').ljust(HEADER_SIZE)
            print(f"[INFO] Sending message of size: {len(size_data)}")
            self.socket.send(size_data)
            print(f"[INFO] Message size sent successfully. Waiting for acknowledgment...")
            # Receive acknowledgment for the size
            if not self.wait_for_ack():
                print("[ERROR] Failed to send message size acknowledgment")
                return

            # Send the message in chunks with retries
            chunk_size = 1024
            remaining_size = size
            for i in range(0, size, chunk_size):
                if remaining_size < chunk_size:
                    chunk_size = remaining_size
                chunk = message_bytes[i:i + chunk_size]
                remaining_size -= chunk_size
                self.socket.send(chunk)

                # Receive acknowledgment for the chunk
                if not self.wait_for_ack():
                    print("[ERROR] Failed to send message chunk acknowledgment. Retrying...")
                    # Retry sending the chunk
                    for retry_count in range(max_retries):
                        time.sleep(retry_interval)
                        self.socket.send(chunk)
                        if self.wait_for_ack():
                            break
                    else:
                        print("[ERROR] Maximum retries reached. Failed to send message chunk.")
                        return

            print(f"[INFO] Message sent successfully.")

        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")

    def receive_data(self):
        try:
            # Receive the size of the incoming message
            size = int(self.socket.recv(1024).decode('utf-8'))
            print(f"[INFO] Receiving message of size: {size}")
            self.send_ack()

            # Receive the message in chunks of 1024 bytes
            data = bytearray()
            while len(data) < size:
                chunk = self.socket.recv(min(1024, size - len(data)))
                if not chunk:
                    print("[ERROR] Connection closed prematurely")
                    return None
                data += chunk

                # Send acknowledgment for the received chunk
                self.send_ack()

            print(f"[INFO] Message received of size: {len(data)}")

            # Decode the received data
            message = data.decode('utf-8')

            return message

        except (socket.error, ValueError) as e:
            print(f"[ERROR] Failed to receive message: {e}")
            return None


    def wait_for_ack(self, timeout=5):
        try:
            ack_message = self.socket.recv(ACKNOWLEDGEMENT_SIZE).strip().decode('utf-8')
            return ack_message == 'ACK'
        except socket.error as e:
            print(f"[ERROR] Failed to receive acknowledgment: {e}")
            return False
    
    def send_ack(self, message="ACK"):
        try:
            ack_message = message
            self.socket.send(ack_message.encode('utf-8').ljust(ACKNOWLEDGEMENT_SIZE))
        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")


w = Worker("192.168.0.100", 9000)
w.send_message("Hello server")
print('message sent')