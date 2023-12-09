import socket
import threading
import json
import time
import hashlib

SERVER_IP = '127.0.0.1'
ID = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_message(server, message):
    try:
        server.send(message.encode('utf-8'))
    except socket.error as e:
        print(f"Failed to send message: {e}")

def execute_task(data):
    print(data["data"])
    result = data["data"].upper()
    message = json.dumps({
        "client_id": ID,
        "type": "result",
        "data": result,
        "task_id": data["task_id"]
    })
    send_message(server, message)


def receive_message(server):
    while True:
        try:
            data = server.recv(1024)
            if not data:
                break
            data = json.loads(data.decode('utf-8'))
            if data["type"] == "task":
                execute_task(data)
            elif data["type"] == "result":
                # print("Result" +data["data"])
                print("Result from client " + str(data["client_id"]) + ": " + data["data"])
        except socket.error:
            break

def send_message_server(server):
    while True:
        # input("Press Enter to send a message to the server... \n")
        # wait for 10ms
        time.sleep(1)

        message = json.dumps({
            "client_id": ID,
            "type": "task",
            "data": "Hello from client"
        })
        send_message(server, message)

def main():
    server.connect((SERVER_IP, 5000))

    connection_message = json.dumps({
        "client_id": ID,
        "type": "commander",
    })

    send_message(server, connection_message)

    recieve_thread = threading.Thread(target=receive_message, args=(server,))
    recieve_thread.start()

    send_thread = threading.Thread(target=send_message_server, args=(server,))
    send_thread.start()

if __name__ == '__main__':
    main()
