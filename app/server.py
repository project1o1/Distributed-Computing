import socket
import threading
from constants import ACKNOWLEDGEMENT_SIZE, HEADER_SIZE

class Server:
    def __init__(self, IP, port):
        self.IP = IP
        self.PORT = port
        self.workers = []
        self.worker_status = []
        self.commanders = []

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.IP, self.PORT))

    def start(self):
        self.server_socket.listen()

        print(f"[INFO] Server listening on {self.IP}:{self.PORT}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            self.send_ack(client_socket,"CONNECTED")  # Send acknowledgment for connection establishment
            client_type = self.receive_message(client_socket)
            self.send_ack(client_socket)  # Send acknowledgment for client type receipt
            if client_type == "worker":
                threading.Thread(target=self.handle_worker, args=(client_socket, client_address)).start()
            elif client_type == "commander":
                threading.Thread(target=self.handle_commander, args=(client_socket, client_address)).start()

    def handle_worker(self, worker_socket, worker_address):
        print(f"[INFO] Connection established with worker {worker_address}")
        worker_id = self.receive_message(worker_socket)
        self.send_ack(worker_socket)
        # self.send_ack(worker_socket, message="CONNECTED")
        # self.send_ack(worker_socket)
        self.workers.append((worker_socket, worker_address, worker_id))
        self.worker_status.append("idle")
        print(f"[INFO] Worker {worker_id} connected to server")

        while True:
            message = self.receive_message(worker_socket)
            if message is None:
                break
            print(f"[INFO] Message received from worker {worker_id}: {message}")

            self.send_ack(worker_socket)
        # Add additional logic as needed for handling worker messages

    def handle_commander(self, commander_socket, commander_address):
        print(f"[INFO] Connection established with commander {commander_address}")
        commander_id = self.receive_message(commander_socket)
        self.send_ack(commander_socket)
        # self.send_ack(commander_socket, message="CONNECTED")
        # self.send_ack(commander_socket)
        self.commanders.append((commander_socket, commander_address, commander_id))
        print(f"[INFO] Commander {commander_id} connected to server")

        while True:
            message = self.receive_message(commander_socket)
            if message is None:
                break
            print(f"[INFO] Message received from commander {commander_id}: {message}")

            # self.send_ack(commander_socket)
        # Add additional logic as needed for handling commander messages

    def receive_message(self, connection):
        try:
            # self.send_ack(connection)  # Send acknowledgment for message size receipt

            size_data = connection.recv(HEADER_SIZE)
            if not size_data:
                print("[ERROR] Failed to receive message size data.")
                return None

            size = int(size_data.strip().decode('utf-8'))

            self.send_ack(connection)  # Send acknowledgment for the message size

            chunks = []
            remaining_size = size
            while remaining_size > 0:
                chunk = connection.recv(min(1024, remaining_size))
                if not chunk:
                    print("[ERROR] Failed to receive message chunk.")
                    return None

                chunks.append(chunk)
                remaining_size -= len(chunk)

                self.send_ack(connection)  # Send acknowledgment for each chunk

            message = b''.join(chunks).decode('utf-8')
            return message

        except socket.error as e:
            print(f"[ERROR] Failed to receive message: {e}")
            return None

    def send_ack(self, conn, message="ACK"):
        try:
            ack_message = message.encode('utf-8').ljust(ACKNOWLEDGEMENT_SIZE)
            conn.send(ack_message)
        except socket.error as e:
            print(f"[ERROR] Failed to send acknowledgment: {e}")

# Example Usage:
s = Server("0.0.0.0", 9001)
s.start()
