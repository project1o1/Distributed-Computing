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
            # data = client_socket.recv(1024).decode('utf-8')
            data = bytearray()
            while True:
                packet = client_socket.recv(1024)
                if not packet:
                    break
                data += packet
            if not data:
                break
            data = json.loads(data)
            if data["message_type"] == "command":
                initial_heights = data["command"]["initial_heights"]
                split_parts = 10
                split_data = [
                    initial_heights[i * len(initial_heights) // split_parts : (i + 1) * len(initial_heights) // split_parts]
                    for i in range(split_parts)
                ]
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
                for task_id in range(tasks.qsize()):
                    assigned = False
                    for soldier_id, soldier_status in self.status.items():
                        if soldier_status == "idle":
                            self.status[soldier_id] = "busy"
                            self.soldiers[soldier_id].send(json.dumps({
                                "message_type": "command",
                                "client_id": client_id,
                                "task_id": task_id,
                                "task": tasks.get()[1]
                            }).encode('utf-8'))
                            assigned = True
                            break
                    if not assigned:
                        tasks.put(tasks.get())  # Re-queue the task for later

    def handle_soldier(self, client_id, client_socket):
        while True:
            # data = client_socket.recv(1024).decode('utf-8')
            data = bytearray()
            while True:
                packet = client_socket.recv(1024)
                if not packet:
                    break
                data += packet
            if not data:
                break
            data = json.loads(data)
            if data["message_type"] == "result":
                self.status[client_id] = "idle"
                if client_id not in self.results:
                    self.results[client_id] = []
                self.results[client_id].append(data)
                if len(self.results[client_id]) == self.metadata[client_id]["length"]:
                    self.results[client_id].sort(key=lambda x: x["task_id"])
                    final_result = [
                        [result["results"][0] for result in self.results[client_id]],
                        [result["results"][1] for result in self.results[client_id]],
                    ]
                    print("[INFO] Sending final result to commander "+str(client_id)+"...")
                    self.commanders[client_id].send(json.dumps({
                        "message_type": "result",
                        "client_id": client_id,
                        "results": final_result
                    }).encode('utf-8'))
                    self.results[client_id] = []
                    del self.metadata[client_id]
    

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



