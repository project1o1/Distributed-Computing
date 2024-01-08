from client import Client
import time
from constants import PORT
import inspect



def uppercase(message : str) -> str:
    return message.upper()

func = inspect.getsource(uppercase)


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
            if user_input.lower() == 'exit':
                break
            user_input = {
                "function": func,
                "function_name": "uppercase",
                "message": "sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal",
            }
            # user_input = input("Enter message to send (or type 'exit' to quit): ")
            # user_input = "sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal sai vishal "
            # time.sleep(.5)
            self.send_message(user_input)

            length = self.receive_message()

            result = {}
            while length > 0:
                result_chunk = self.receive_message()
                result[result_chunk["chunk_number"]] = result_chunk
                print(f"[INFO] Received chunk {result_chunk['chunk_number']}")
                length -= 1

            message = ""
            for i in range(len(result)):
                message += result[i]["message"]+" "
            print(f"[INFO] Result received from server: {message}")

c = Commander("127.0.0.1", PORT)

