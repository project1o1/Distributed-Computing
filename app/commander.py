from client import Client
import time

class Commander(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "commander"
        self.socket.connect((self.IP, self.port))
        if self.wait_for_ack(expected_ack="CONNECTED"):
            self.send_message(self.type)
            if self.wait_for_ack():
                self.send_message(self.ID)
                if self.wait_for_ack():
                    print(f"[INFO] Client {self.ID} connected to server")
                    self.start_message_loop()
                else:
                    print(f"[ERROR] Failed to connect to server")
                    exit(1)
            else:
                print(f"[ERROR] Failed to connect to server")
                exit(1)
        else:
            print(f"[ERROR] Failed to connect to server")
            exit(1)

    def start_message_loop(self):
        while True:
            # user_input = input("Enter message to send (or type 'exit' to quit): ")
            user_input = "hello"
            # time.sleep(.5)
            if user_input.lower() == 'exit':
                break
            self.send_message(user_input)


c = Commander("127.0.0.1", 9001)