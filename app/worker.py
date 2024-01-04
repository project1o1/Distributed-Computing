import socket
import nanoid

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

    def send_message(self, message):
        try:
            message = message.encode('utf-8')
            ack_message = self.receive_message()
            if ack_message == 'ACK':
                print(f"[INFO] Sending message: {message}")
                self.socket.send(message)
                print(f"[INFO] Message sent.")
            else:
                print("[ERROR] Failed to send message")
        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")
    
    def receive_message(self, size = 1024):
        try:
            message = self.socket.recv(size).decode('utf-8')
            return message
        except socket.error:
            print("[ERROR] Failed to receive message")
            return None
