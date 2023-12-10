import socket
import queue
import json
from threading import Thread, Lock

class General:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))

        # self.clients = []
        self.commanders = {}
        self.soldiers = {}
        self.status = {}
        self.metadata = {}
        self.results = {}
        # self.tasks = queue.Queue()
        # self.tasks_lock = Lock()

    def handle_commander(self, client_id, client_socket):
        tasks = queue.Queue()
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            data = json.loads(data)
            if data["message_type"] == "command":
                for i, word in enumerate(data["command"].split()):
                    tasks.put((i, word))
                self.metadata[data["client_id"]] = {
                    "length" : tasks.qsize(),
                }
                for j in range(tasks.qsize()):
                    i = 0
                    task = tasks.get()
                    while i < len(self.status):
                        c_id = list(self.status.keys())[i]
                        if self.status[c_id] == "idle":
                            self.status[c_id] = "busy"
                            self.soldiers[c_id].send(json.dumps({
                                "message_type": "command",
                                "client_id" : client_id,
                                "task_id": task[0],
                                "task": task[1]
                            }).encode('utf-8'))
                            break
                        i += 1
                        if i == len(self.status):
                            i = 0
    
    def handle_soldier(self, client_id, client_socket):
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            data = json.loads(data)
            if data["message_type"] == "result":
                self.status[client_id] = "idle"
                if data["client_id"] not in self.results:
                    self.results[data["client_id"]] = []
                self.results[data["client_id"]].append(data)
                if len(self.results[data["client_id"]]) == self.metadata[data["client_id"]]["length"]:
                    # sort the results[data["client_id"]]] according to task_id
                    self.results[data["client_id"]].sort(key=lambda x: x["task_id"])
                    final_result = ' '.join([result["result"] for result in self.results[data["client_id"]]])
                    self.commanders[data["client_id"]].send(json.dumps({
                        "message_type": "result",
                        "client_id": client_id,
                        "results": final_result
                    }).encode('utf-8'))
                    self.results[data["client_id"]] = []
                    self.metadata[data["client_id"]] = {}

    

    def accept_client(self):
        client_socket, client_address = self.socket.accept()
        # print("Accepted connection from: " + str(client_address))

        # Extract "client_id" from the incoming data
        data = json.loads(client_socket.recv(1024).decode('utf-8'))
        client_id = data['client_id']
        type = data['type']
        if type == "commander":
            print(f'[INFO] New commander: {client_address}')
            self.commanders[client_id] = client_socket
            thread = Thread(target=self.handle_commander, args=(client_id, client_socket))
            thread.start()
        elif type == "soldier":
            print(f'[INFO] New soldier: {client_address}')
            self.soldiers[client_id] = client_socket
            self.status[client_id] = "idle"
            thread = Thread(target=self.handle_soldier, args=(client_id, client_socket))
            thread.start()


