import socket
import json
import numpy as np 
import pickle
import base64
import sys
import time
class Client:
    def __init__(self, IP, port, ID):
        self.IP = IP
        self.port = port
        self.ID = ID
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.IP, self.port))

    def send_message(self,message):
        try:
            print("message size(bytes): ", sys.getsizeof(message))
            self.server.send(message.encode('utf-8'))
        except socket.error as e:
            print(f"[ERROR] Failed to send message: {e}")

    def recv(self):
        return self.server.recv(1024).decode()

    def close(self):
        self.server.close()

    def __del__(self):
        self.close()

    def receive_message(self):
        try:
            size = self.server.recv(1024).decode('utf-8')
            # size = json.loads(size)
            size = int(size)
            print('Size: ', size)
            data = bytearray()
            while size - len(data) >= 1024:
                packet = self.server.recv(1024)
                # print('[INFO] Packet received')
                if not packet:
                    break
                data += packet
            if size - len(data) > 0:
                packet = self.server.recv(size-len(data))
                if not packet:
                    pass
                else:
                    data += packet
            print('Size of data: ', len(data))
            data = json.loads(data.decode('utf-8'))
            if not data:
                return None
            # data = json.loads(data.decode('utf-8'))
            return data
        except socket.error:
            print("[ERROR] Failed to receive message")
            return None


class Commander(Client):
    def __init__(self, server, port, ID):
        super().__init__(server, port, ID)
        self.type = "commander"
        self.send_message(json.dumps({
            "message_type": "connection",
            "client_id": self.ID,
            "type": self.type
        }))

    def command(self, command):
        try:
            message = json.dumps(json.dumps({
                "message_type": "command",
                "client_id": self.ID,
                "command": command
            }))
            self.send_message(str(sys.getsizeof(message)))
            time.sleep(0.1)
            self.send_message(message)

            data = self.receive_message()
            if data["message_type"] == "result":
                return data
            else:
                print("[ERROR] Failed to receive result")
                print("[INFO] Retrying...")
                return self.command(self.ID, command)

        except socket.error:
            print("[ERROR] Failed to send command")
            return None
        

class Soldier(Client):
    def __init__(self, server, port, ID):
        super().__init__(server, port, ID)
        self.type = "soldier"
        self.send_message(json.dumps({
            "message_type": "connection",
            "client_id": self.ID,
            "type": self.type
        }))
        self.task = None

    def receive_orders(self):
        try:
            size = self.server.recv(1024).decode('utf-8')
            # size = json.loads(size)
            print('Size: ', size)
            size = int(size)
            print('Size: ', size)
            
            # Receive the entire data in one go
            # data = self.server.recv(size).decode('utf-8')
            data = bytearray()
            while size - len(data) >= 1024:
                packet = self.server.recv(1024)
                if not packet:
                    break
                data += packet
            if size - len(data) > 0:
                packet = self.server.recv(size-len(data))
                if not packet:
                    pass
                else:
                    data += packet
            # print('Size of data: ', len(data))
            try:
                # Deserialize the JSON directly
                data = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"[WARNING] JSON decoding error: {e}")
                print("[INFO] Attempting to strip extra characters and retrying...")
                
                # Attempt to strip extra characters and retry
                data = json.loads(data[:e.pos])

            if data["message_type"] == "command":
                self.task = data
                return self.obey(data)
            else:
                print("[ERROR] Failed to receive command")
                print("[INFO] Retrying...")
                return self.receive_orders()

        except socket.error:
            print("[ERROR] Failed to receive command")
            return None

    def obey(self, task):
        try:
            # result = task["task"].upper()
            sim_task = (task["task"])
            # print("sim_task: ", sim_task)
            simulator = sim_task["function"]
            serialized_function = base64.b64decode(simulator)
            simulator = pickle.loads(serialized_function)
            simulator_args = {}
            for key in sim_task:
                if key != "function":
                    simulator_args[key] = sim_task[key]
            
            result = simulator(**simulator_args)

            # self.send_message(json.dumps({
            #     "message_type": "result",
            #     "client_id": task["client_id"],   
            #     "result": result,
            #     "task_id": task["task_id"]
            # }))

            message = json.dumps({
                "message_type": "result",
                "client_id": task["client_id"],
                "result": result,
                "task_id": task["task_id"]
            })
            self.send_message(str(sys.getsizeof(message.encode('utf-8'))))
            self.send_message(message)

            return task["task_id"]
        except socket.error:
            print("[ERROR] Failed to send result")
            return None
