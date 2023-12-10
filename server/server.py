import socket
import queue
import json
from threading import Thread
import sys
import time

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
            # data = client_socket.recv(1024).decode('utf-8')
            size = client_socket.recv(1024).decode('utf-8')
            # size = json.loads(size)
            size = int(size)
            print('Size for commander: ', size)
            data = bytearray()
            while size - len(data) >= 1024:
                packet = client_socket.recv(1024)
                if not packet:
                    break
                data += packet
            if size - len(data) > 0:
                packet = client_socket.recv(size-len(data))
                if not packet:
                    break
                data += packet
            # print('Size of data: ', len(data))
            # print(type(data))
            data = data.decode('utf-8')
            # print(type(data))
            data = json.loads(data)
            # print(type(data))
            data = json.loads(data)
            # print(type(data))
            if data["message_type"] == "command":
                initial_heights = data["command"]["initial_heights"]
                split_parts = 10
                split_data = [
                    initial_heights[i * len(initial_heights) // split_parts : (i + 1) * len(initial_heights) // split_parts]
                    for i in range(split_parts)
                ]
                print('[INFO] Split data into '+str(len(split_data))+' parts')
                for i, heights_part in enumerate(split_data):
                    tasks.put((i, {
                        "function": data["command"]["function"],
                        "num_steps": data["command"]["num_steps"],
                        "num_balls": len(heights_part),
                        "damping_factor": data["command"]["damping_factor"],
                        "dt": data["command"]["dt"],
                        "initial_heights": heights_part
                    }))

                # Store metadata for the client
                self.metadata[data["client_id"]] = {
                    "length": tasks.qsize(),
                }

                # Assign tasks to available soldiers
                # for task_id in range(tasks.qsize()):
                # num_tasks = tasks.qsize()
                # task_id = 0
                # num_tasks = tasks.qsize()
                # while task_id <= num_tasks:
                #     # assigned = False
                #     for soldier_id, soldier_status in self.status.items():
                #         if soldier_status == "idle":
                #             task = tasks.get()
                #             self.status[soldier_id] = "busy"
                #             command = json.dumps({
                #                 "message_type": "command",
                #                 "client_id": client_id,
                #                 "task_id": task_id,
                #                 "task": task[1]
                #             }).encode('utf-8')
                #             self.soldiers[soldier_id].send(str(sys.getsizeof(command)).encode('utf-8'))
                #             time.sleep(0.1)
                #             self.soldiers[soldier_id].send(command)
                #             # assigned = True
                #             task_id += 1
                #             break
                    # if not assigned:
                    #     tasks.put(task)  # Re-queue the task for later
                length = len(self.soldiers)
                soldier_ids = list(self.status.keys())
                num_tasks = tasks.qsize()
                i=0
                task_id = 0
                while i<length and task_id < num_tasks: 
                    if self.status[soldier_ids[i]] == "idle":
                        self.status[soldier_ids[i]] = "busy"
                        task = tasks.get()
                        command = json.dumps({
                            "message_type": "command",
                            "client_id": client_id,
                            "task_id": task_id,
                            "task": task[1]
                        }).encode('utf-8')
                        self.soldiers[soldier_ids[i]].send(str(sys.getsizeof(command)).encode('utf-8'))
                        time.sleep(0.1)
                        self.soldiers[soldier_ids[i]].send(command)
                        task_id += 1
                    i+=1
                    if i == length:
                        i = 0
                    



    def handle_soldier(self, client_id, client_socket):
        while True:
            # data = client_socket.recv(1024).decode('utf-8')
            size = client_socket.recv(1024).decode('utf-8')
            # size = json.loads(size)
            # print('Size for soldier: ', size)
            size = int(size)
            data = bytearray()
            while size - len(data) >= 1024:
                packet = client_socket.recv(1024)
                if not packet:
                    break
                data += packet
            if size - len(data) > 0:
                packet = client_socket.recv(size-len(data))
                if not packet:
                    break
                data += packet
            print('Size from soldier: ', len(data))
            # print(self.metadata)
            # print(self.status)
            data = json.loads(data)
            if data["message_type"] == "result":
                c_id = data["client_id"]
                self.status[client_id] = "idle"
                if c_id not in self.results:
                    self.results[c_id] = []
                self.results[c_id].append(data)
                # time.sleep(0.1)
                if len(self.results[c_id]) == self.metadata[c_id]["length"]:
                    self.results[c_id].sort(key=lambda x: x["task_id"])
                    print("[INFO] Received all results from soldier "+str(client_id))
                    final_result = [
                        [result["result"][0] for result in self.results[c_id]],
                        [result["result"][1] for result in self.results[c_id]],
                    ]
                    print("[INFO] Sending final result to commander "+str(c_id)+"...")

                    # self.commanders[client_id].send(json.dumps({
                    #     "message_type": "result",
                    #     "client_id": client_id,
                    #     "results": final_result
                    # }).encode('utf-8'))
                    
                    # print(final_result)

                    message = json.dumps({
                        "message_type": "result",
                        "client_id": c_id,
                        "results": final_result
                    }).encode('utf-8')
                    self.commanders[c_id].send(str(sys.getsizeof(message)).encode('utf-8'))
                    time.sleep(0.1)
                    self.commanders[c_id].send(message)
                    self.results[c_id] = []
                    del self.metadata[c_id]
    

    def accept_client(self):
        client_socket, client_address = self.socket.accept()

        try:
            data = json.loads(client_socket.recv(1024).decode('utf-8'))
            client_id = data['client_id']
            client_type = data['type']

            if client_type == "commander":
                print(f'[INFO] New commander: {client_address}')
                self.commanders[client_id] = client_socket
                thread = Thread(target=self.handle_commander, args=(client_id, client_socket))
                thread.start()
            elif client_type == "soldier":
                print(f'[INFO] New soldier: {client_address}')
                self.soldiers[client_id] = client_socket
                self.status[client_id] = "idle"
                thread = Thread(target=self.handle_soldier, args=(client_id, client_socket))
                thread.start()

        except (ValueError, KeyError):
            print("[ERROR] Invalid data received from client.")
            client_socket.close()



