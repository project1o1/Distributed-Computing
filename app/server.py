import socket
from constants import ACKNOWLEDGEMENT_SIZE, HEADER_SIZE

class Server:
    def __init__(self, IP, port):
        self.IP = IP
        self.PORT = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.IP, self.PORT))


    def accept_connection(self):
        self.socket.listen(1)
        connection, address = self.socket.accept()
        self.send_ack(connection)
        connection.recv(ACKNOWLEDGEMENT_SIZE)
        print(f"[INFO] Connection established with {address}")
        return connection, address
    
    def receive_message(self, con:socket.socket):
        try:
            print("[INFO] Receiving message size.")
            size_data = con.recv(HEADER_SIZE)
            if not size_data:
                print("[ERROR] Failed to receive message size data.")
                return None
            print(f'[INFO] Message size received successfully.{size_data}')

            size = int(size_data.strip().decode('utf-8'))
            print(f"[INFO] Receiving message of size {size}.")

            self.send_ack(con)

            chunks = []
            remaining_size = size
            while remaining_size > 0:
                chunk = con.recv(min(1024, remaining_size))
                if not chunk:
                    print("[ERROR] Failed to receive message chunk.")
                    return None

                chunks.append(chunk)
                remaining_size -= len(chunk)

                self.send_ack(con)

            message = b''.join(chunks).decode('utf-8')
            print("[INFO] Message received successfully.")

            return message

        except socket.error as e:
            print(f"[ERROR] Failed to receive message: {e}")
            return None
    
    def send_ack(self, conn:socket.socket, message="ACK"):
        try:
            ack_message = message.encode('utf-8').ljust(ACKNOWLEDGEMENT_SIZE)
            conn.send(ack_message)
        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")


s = Server("0.0.0.0", 9000)
connection, address = s.accept_connection()
print(s.receive_message(connection))