# server.py
import socket
import threading
from constants import ACKNOWLEDGEMENT_SIZE, HEADER_SIZE, PORT
import time
from queue import Queue
from threading import Lock
import nanoid
import json

class Server:
    def __init__(self, IP, port):
        self.IP = IP
        self.PORT = port
        self.workers = []
        self.worker_status = {}
        self.commanders = {}
        self.commander_status = {}

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.IP, self.PORT))
        self.message_queue = Queue()
        self.result_queue = Queue()
        self.all_messages = {}

        self.result_lengths = {}
        self.result_sent_lengths = {}

        # self.lock = Lock()
        # self.result_lock = Lock()

    def start(self):
        self.server_socket.listen()
        print(f"[INFO] Server listening on {self.IP}:{self.PORT}")
        threading.Thread(target=self.handle_result_queue).start()
        threading.Thread(target=self.order_messages).start()
        while True:
            client_socket, client_address = self.server_socket.accept()
            self.send_ack(client_socket, "CONNECTED")  # Send acknowledgment for connection establishment
            client_type = self.receive_message(client_socket)
            self.send_ack(client_socket)  # Send acknowledgment for client type receipt

            if client_type == "worker":
                worker_id = self.receive_message(client_socket)
                self.send_ack(client_socket)
                # self.lock.acquire()
                self.workers.append((client_socket, client_address, worker_id))
                self.worker_status[worker_id] = "idle"
                # self.lock.release()
                print(f"[INFO] Worker {worker_id} connected to server")

                threading.Thread(target=self.handle_worker_send, args=(client_socket, client_address, worker_id)).start()
                # threading.Thread(target=self.handle_worker_receive, args=(client_socket, client_address, worker_id)).start()

            elif client_type == "commander":
                threading.Thread(target=self.handle_commander, args=(client_socket, client_address)).start()

    def handle_result_queue(self):
        while True:
            result = self.result_queue.get()
            # print(f"[INFO] Result Queue size: {self.result_queue.qsize()}")
            commander_id = result["commander_id"]
            if self.commander_status[commander_id] == "idle":
                self.result_queue.put(result)
                continue
            self.commander_status[commander_id] = "busy"
            commander_socket, commander_address = self.commanders[commander_id]
            # self.send_ack(commander_socket, "RESULT")
            self.send_message(result, commander_socket)
            # print(f"[INFO] Result sent to commander {commander_id}")
            # self.commander_status[commander_id] = "idle"
            self.result_sent_lengths[commander_id] += 1
            if self.result_sent_lengths[commander_id] == self.result_lengths[commander_id]:
                self.commander_status[commander_id] = "idle"
            # print(f"[INFO] Result is {result}")

    def handle_worker_send(self, worker_socket, worker_address, worker_id):
        while True:
            if self.worker_status[worker_id] == "busy":
                continue

            # self.lock.acquire()
            if not self.message_queue.empty():
                message = self.message_queue.get()
                # print(f"[INFO] Message removed from message queue")
                self.send_message(message, worker_socket)
                self.worker_status[worker_id] = "busy"
                # print(f"[INFO] Message sent to worker {worker_address}")
                self.handle_worker_receive(worker_socket, worker_address, worker_id)
            # self.lock.release()

    def handle_worker_receive(self, worker_socket, worker_address, worker_id):
        if self.wait_for_ack(worker_socket):
            # print(f"[INFO] Acknowledgment received from worker {worker_address}")
            result = self.receive_message(worker_socket)
            result["timestamp"] = time.time()
            self.result_queue.put(result)
            # print(f"[INFO] Result received from worker {worker_address}: {result}")
            self.worker_status[worker_id] = "idle"
        
        # while True:
            # message = self.receive_message(worker_socket)
            # if message is None:
            #     break
            # self.lock.acquire()
            # print(f"[INFO] Message received from worker {worker_address}: {message}")
            # self.result_queue.put(message)
            # print(f"[INFO] Message added to result queue")

    def handle_commander(self, commander_socket, commander_address):
        # print(f"[INFO] Connection established with commander {commander_address}")
        commander_id = self.receive_message(commander_socket)
        self.send_ack(commander_socket)
        # self.lock.acquire()
        # self.commanders.append((commander_socket, commander_address, commander_id))
        self.commanders[commander_id] = (commander_socket, commander_address)
        self.commander_status[commander_id] = "idle"
        # print(f"[INFO] Commander {commander_id} connected to server")
        # self.lock.release()

        while True:
            if self.commander_status[commander_id] == "busy":
                continue
            message = self.receive_message(commander_socket)
            if message is None:
                break
            # print(f"[INFO] Message received from commander {commander_id}: {message}")
            input_task = message["message"]
            no_of_chunks = len(input_task) if len(input_task)<10 else 20
            # message_chunks = [string[i:i + len(string)//no_of_chunks] for i in range(0, len(string), len(string)//no_of_chunks)]
            # input_task is a list of values, divide it into chunks
            message_chunks = [input_task[i:i + len(input_task)//no_of_chunks] for i in range(0, len(input_task), len(input_task)//no_of_chunks)]
            self.send_message(len(message_chunks), commander_socket)
            # print(f"[INFO] Message length sent to commander {commander_id}")
            self.all_messages[commander_id] = Queue()
            for index, message_chunk in enumerate(message_chunks):
                chunk = message.copy()
                chunk["message"] = message_chunk
                self.add_message_to_queue(chunk, commander_id, index)
            self.result_lengths[commander_id] = len(message_chunks)
            self.result_sent_lengths[commander_id] = 0
            self.commander_status[commander_id] = "busy"

    def add_message_to_queue(self, message, commander_id, index):
        message_received = {
                "commander_id": commander_id,
                "message": message,
                "timestamp": time.time(),
                "message_id": nanoid.generate(size=10),
                "message_type": "task",
                "chunk_number": index
            }
        # self.message_queue.put(message_received)
        self.all_messages[commander_id].put(message_received)
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

            message_bytes = b''.join(chunks)
            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)  # Decode the JSON message

            return message

        except socket.error as e:
            print(f"[ERROR] Failed to receive message: {e}")
            return None

    def send_message(self, message, conn, max_retries=3, retry_interval=1):
        try:
            # Convert message to bytes using JSON serialization
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')

            # Send the size of the message
            size = len(message_bytes)
            size_data = str(size).encode('utf-8').ljust(HEADER_SIZE)
            # print(f"[INFO] Sending message of size: {len(size_data)}")
            conn.send(size_data)
            # print(f"[INFO] Message size sent successfully. Waiting for acknowledgment...")

            # Receive acknowledgment for the size
            if not self.wait_for_ack(conn):
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
                conn.send(chunk)

                # Receive acknowledgment for the chunk
                if not self.wait_for_ack(conn):
                    print("[ERROR] Failed to send message chunk acknowledgment. Retrying...")
                    # Retry sending the chunk
                    for retry_count in range(max_retries):
                        time.sleep(retry_interval)
                        conn.send(chunk)
                        if self.wait_for_ack(conn):
                            break
                    else:
                        print("[ERROR] Maximum retries reached. Failed to send message chunk.")
                        return

            # print(f"[INFO] Message sent successfully.")

        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")

    def send_ack(self, conn, message="ACK"):
        try:
            ack_message = message.encode('utf-8').ljust(ACKNOWLEDGEMENT_SIZE)
            conn.send(ack_message)
        except socket.error as e:
            print(f"[ERROR] Failed to send acknowledgment: {e}")

    def wait_for_ack(self, conn, expected_ack="ACK"):
        try:
            ack = conn.recv(ACKNOWLEDGEMENT_SIZE)
            return ack.decode('utf-8').strip() == expected_ack
        except socket.error as e:
            print(f"[ERROR] Failed to receive acknowledgment: {e}")
            return False

s = Server("0.0.0.0", port=PORT)
s.start()
