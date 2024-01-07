import socket
from constants import ACKNOWLEDGEMENT_SIZE, HEADER_SIZE

class Server:
    def __init__(self, IP, port):
        self.IP = IP
        self.PORT = port
        self.workers = []
        self.worker_status = []
        self.commanders = []
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.IP, self.PORT))

    def accept_connection(self):
        self.socket.listen(1)
        connection, address = self.socket.accept()
        print(f"[INFO] Connection established with {address}")
        self.send_ack(connection, message="CONNECTED")
        id = self.receive_message(connection)
        self.send_ack(connection)
        type = self.receive_message(connection)
        self.send_ack(connection)
        # return connection, address, id, type
        if type == "worker":
            self.workers.append((connection, address, id))
            self.worker_status.append("idle")
        elif type == "commander":
            self.commanders.append((connection, address, id))
        return connection, address, id, type

    def receive_message(self, con: socket.socket):
        try:
            print("[INFO] Receiving message size acknowledgment.")
            self.send_ack(con)  # Send acknowledgment for message size receipt

            size_data = con.recv(HEADER_SIZE)
            if not size_data:
                print("[ERROR] Failed to receive message size data.")
                return None

            size = int(size_data.strip().decode('utf-8'))
            print(f'[INFO] Message size received successfully: {size}')
            print(f"[INFO] Receiving message of size {size}.")

            self.send_ack(con)  # Send acknowledgment for the message size

            chunks = []
            remaining_size = size
            while remaining_size > 0:
                chunk = con.recv(min(1024, remaining_size))
                if not chunk:
                    print("[ERROR] Failed to receive message chunk.")
                    return None

                chunks.append(chunk)
                remaining_size -= len(chunk)

                self.send_ack(con)  # Send acknowledgment for each chunk

            message = b''.join(chunks).decode('utf-8')
            print("[INFO] Message received successfully.")
            print(f"[INFO] Message: {message}")
            return message

        except socket.error as e:
            print(f"[ERROR] Failed to receive message: {e}")
            return None

    def send_ack(self, conn: socket.socket, message="ACK"):
        try:
            ack_message = message.encode('utf-8').ljust(ACKNOWLEDGEMENT_SIZE)
            conn.send(ack_message)
        except socket.error as e:
            print(f"[ERROR] Failed to send acknowledgment: {e}")


s = Server("0.0.0.0", 9000)
# connection, address, id, type = s.accept_connection()
# print("[INFO] Details of the client:")
# print(f"IP Address: {address[0]}")
# print(f"Port: {address[1]}")
# print(f"ID: {id}")
# print(f"Type: {type}")
# print("[INFO] Receiving message from client...")
# print(s.receive_message(connection))
while True:
    connection, address, id, type = s.accept_connection()
    print("[INFO] Details of the client:")
    print(f"IP Address: {address[0]}")
    print(f"Port: {address[1]}")
    print(f"ID: {id}")
    print(f"Type: {type}")
    print("[INFO] Receiving message from client...")
    print(s.receive_message(connection))
