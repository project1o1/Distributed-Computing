from client import Client
from constants import PORT

class Worker(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "worker"
        self.socket.connect((self.IP, self.port))
        if self.wait_for_ack(expected_ack="CONNECTED"):
            self.send_message(self.type)
            if self.wait_for_ack():
                self.send_message(self.ID)
                if self.wait_for_ack():
                    print(f"[INFO] Client {self.ID} connected to server")
                    # self.start_message_loop()
                    self.start_task_loop()
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
            user_input = input("Enter message to send (or type 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break
            self.send_message(user_input)
    
    def start_task_loop(self):
        while True:
            message = self.receive_message()
            if message is None:
                break
            print(f"[INFO] Message received: {message}")
            task = message["message"]
            input_task = task["message"]
            function = task["function"]
            function_name = task["function_name"]
            exec(function)
            result = eval(function_name+"(input_task)")
            self.send_ack()
            message["message_type"] = "result"
            message["message"] = result
            self.send_message(message)
            # if message["message_type"] == "task":
            #     self.send_ack()
            #     self.send_ack()

w = Worker("127.0.0.1", PORT)
