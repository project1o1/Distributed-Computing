import socket
import json
import numpy as np 
import pickle
import base64
import sys
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
            # data = self.server.recv(1024)
            data = bytearray()
            while True:
                print("packet")
                packet = self.server.recv(1024)
                if not packet:
                    break
                data += packet
            if not data:
                return None
            data = json.loads(data.decode('utf-8'))
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
            self.send_message(json.dumps({
                "message_type": "command",
                "client_id": self.ID,
                "command": command
            }))

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
            data = self.receive_message()
            if data["message_type"] == "command":
                self.task = data
                # return data
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
            sim_task = json.loads(task["task"])

            simulator = sim_task["function"]
            serialized_function = base64.b64decode(simulator)
            simulator = pickle.loads(serialized_function)
            simulator_args = {}
            for key in sim_task:
                if key != "function":
                    simulator_args[key] = sim_task[key]
            
            result = simulator(**simulator_args)

            self.send_message(json.dumps({
                "message_type": "result",
                "client_id": task["client_id"],
                "result": result,
                "task_id": task["task_id"]
            }))
            return task["task_id"]
        except socket.error:
            print("[ERROR] Failed to send result")
            return None
