from client import Client

class Commander(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "commander"
        self.socket.connect((self.IP, self.port))
        if self.wait_for_ack(expected_ack="CONNECTED"):
            self.send_message(self.ID)
            if self.wait_for_ack():
                self.send_message(self.type)
                if self.wait_for_ack():
                    print(f"[INFO] Client {self.ID} connected to server")
                else:
                    print(f"[ERROR] Failed to connect to server")
                    exit(1)
            else:
                print(f"[ERROR] Failed to connect to server")
                exit(1)
        else:
            print(f"[ERROR] Failed to connect to server")
            exit(1)

c = Commander("127.0.0.1", 9000)
c.send_message("Hello server")
print('message sent')