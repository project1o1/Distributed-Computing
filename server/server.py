import socket
import queue
import json
from threading import Thread

class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))

        self.clients = []
        self.status = []
        # self.tasks = queue.Queue()
        # self.results = queue.Queue()

    def client_handler(self, client_socket, client_address):
        tasks = queue.Queue()
        results = queue.Queue()

        def distribute_task(tasks):
            while True:
                if tasks.empty():
                    continue
                task = tasks.get()
                words = task["data"].split()
                for i, word in enumerate(words):
                    data = json.dumps({
                        "client_id" : task["client_id"],
                        "task_id" : i,
                        "type" : task["type"],
                        "data" : word
                    })
                    for client_index, client in enumerate(self.clients):
                        if self.status[client_index] == "idle":
                            client.send(data.encode())
                            self.status[client_index] = "busy"
                            break
                    
        
        def gather_result():
            while True:
                if results.empty():
                    continue
                result = results.get()
                result = json.loads(result.decode())
        
        task_distribution_thread = Thread(target=distribute_task, args=(tasks,))
        task_distribution_thread.start()

        gather_result_thread = Thread(target=gather_result, args=(results,))
        gather_result_thread.start()

        while True:
            data = client_socket.recv(1024)
            if not data:
                continue
            print("Received data from " + str(client_address) + ": " + data.decode())
            tasks.put(json.loads(data.decode()))
    
    def accept_client(self):
        client_socket, client_address = self.socket.accept()
        print("Accepted connection from: " + str(client_address))
        self.clients.append(client_socket)
        self.status.append("idle")

        client_thread = Thread(target=self.client_handler, args=(self, client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    server = Server("0.0.0.0", 5000)
