import socket
import queue
import json
from threading import Thread, Lock

class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))

        self.clients = []
        self.status = []
        self.tasks = queue.Queue()
        self.tasks_lock = Lock()

    def client_handler(self, client_socket, client_address):
        def distribute_task(tasks):
            while True:
                if tasks.empty():
                    continue
                task = tasks.get()
                words = task["data"].split()
                with self.tasks_lock:
                    for i, word in enumerate(words):
                        data = json.dumps({
                            "client_id": task["client_id"],
                            "task_id": i,
                            "type": task["type"],
                            "data": word
                        })
                        for client_index, client in enumerate(self.clients):
                            if self.status[client_index] == "idle":
                                client.send(data.encode())
                                self.status[client_index] = "busy"

        def gather_result(results):
            while True:
                if results.empty():
                    continue
                result = results.get()

                # Check if 'task_id' key exists in the result dictionary
                task_id = result.get("task_id", None)
                if task_id is None:
                    print("Received result without task_id:", result)
                    continue
                
                data = json.dumps({
                    "client_id": result["client_id"],
                    "task_id": task_id,
                    "type": result["type"],
                    "data": result["data"]
                })

                for client_index, client in enumerate(self.clients):
                    if self.status[client_index] == "busy" and result["client_id"] == client_index:
                        client.send(data.encode())
                        self.status[client_index] = "idle"
                        break



        task_distribution_thread = Thread(target=distribute_task, args=(self.tasks,))
        task_distribution_thread.start()

        gather_result_thread = Thread(target=gather_result, args=(self.tasks,))
        gather_result_thread.start()

        while True:
            data = client_socket.recv(1024)
            if not data:
                continue
            print("Received data from " + str(client_address) + ": " + data.decode())
            data = json.loads(data.decode())
            if data["type"] == "task":
                with self.tasks_lock:
                    # Add the task to the queue
                    self.tasks.put(data)
                    # Update the queue size
                    print("Task added to queue")
                    print("Queue size:", self.tasks.qsize())
            elif data["type"] == "result":
                self.status[data["client_id"]] = "idle"
                print("Received result from client " + str(data["client_id"]) + ": " + data["data"])
                #send it back to the original client
                client_socket.send(data.encode())

    def accept_client(self):
        client_socket, client_address = self.socket.accept()
        print("Accepted connection from: " + str(client_address))

        # Extract "client_id" from the incoming data
        data = json.loads(client_socket.recv(1024).decode('utf-8'))
        client_id = data["client_id"]

        # Ensure the status list has enough elements for the client's client_id
        while len(self.status) <= client_id:
            self.status.append("")

        self.clients.append(client_socket)
        self.status[client_id] = "idle"

        client_thread = Thread(target=self.client_handler, args=(client_socket, client_id))
        client_thread.start()


if __name__ == "__main__":
    server = Server("0.0.0.0", 5000)

    try:
        server.socket.listen(5)

        while True:
            server.accept_client()

    except KeyboardInterrupt:
        print("Server shutting down.")

    finally:
        server.socket.close()
