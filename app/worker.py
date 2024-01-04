import socket
import nanoid
import time

class Worker:
    def __init__(self, serverIP, port, ID):
        self.serverIP = serverIP
        self.port = port
        self.ID = nanoid.generate(size=10)
        self.type = "worker"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.serverIP, self.port))
        # self.socket.send(self.ID.encode('utf-8'))
        self.send_message(self.ID)
        print(f"[INFO] Worker {self.ID} connected to server")
        self.socket.recv(1024).decode('utf-8')

    def send_message(self, message, max_retries=3, retry_interval=1):
        try:
            # Convert message to bytes
            message_bytes = message.encode('utf-8')

            # Send the size of the message
            size = len(message_bytes)
            size_data = str(size).encode('utf-8')
            self.socket.send(size_data)

            # Receive acknowledgment for the size
            if not self.wait_for_ack():
                print("[ERROR] Failed to send message size acknowledgment")
                return

            # Send the message in chunks with retries
            chunk_size = 1024
            for i in range(0, size, chunk_size):
                chunk = message_bytes[i:i + chunk_size]
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
            ack_message = self.socket.recv(1024).decode('utf-8')
            return ack_message == 'ACK'
        except socket.error as e:
            print(f"[ERROR] Failed to receive acknowledgment: {e}")
            return False
    
    def send_ack(self):
        try:
            ack_message = 'ACK'
            self.socket.send(ack_message.encode('utf-8'))
        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")

    def receive_ack(self):
        try:
            message = self.socket.recv(1024).decode('utf-8')
            return message
        except socket.error as e:
            print(f"[ERROR] Failed to receive message: {e}")
            return None

