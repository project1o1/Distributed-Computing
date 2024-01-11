from client import Client
import time
from constants import PORT
import base64

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
            user_input = input("Press Enter to send the function (or type 'exit' to quit): ")
            
            # read file
            f = open("./cube_diorama/cube_diorama.blend", "rb")
            file = f.read()

            start = time.time()

            message = {
                # "file": file,
                "file_name": "cube_diorama.blend",
                "file": base64.b64encode(file).decode('utf-8'),
                "start_frame": 1,
                "end_frame": 50,
                }
            # send file
            self.send_message(message)
            print(f"[INFO] File sent to server")




            # # self.send_message(user_input)
            # length = self.receive_message()

            # result = {}
            # while length > 0:
            #     result_chunk = self.receive_message()
            #     result[result_chunk["chunk_number"]] = result_chunk
            #     print(f"[INFO] Received chunk {result_chunk['chunk_number']}")
            #     length -= 1
            # end = time.time()

c = Commander("127.0.0.1", PORT)

