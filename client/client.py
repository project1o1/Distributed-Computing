import socket
import threading
import json

SERVER_IP = '192.168.0.107'
ID = 1
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_message(server, message):
    try:
        server.send(message.encode('utf-8'))
    except socket.error as e:
        print(f"Failed to send message: {e}")

def execute_task(data):
    print(data.data)
    # Upper case the data and return it to the server
    result = data.data.upper()
    message = json.dumps({
        "client_id": ID,
        "type": "result",
        "data": result,
        "task_id": data.task_id
    })
    # server.send(message.encode('utf-8'))
    send_message(server, message)


def recieve_message(server):
    while True:
        try:
            data = server.recv(1024)
            if not data:
                break
            data = json.loads(data.decode('utf-8'))
            if data.type == "task":
                # print(data.data)
                execute_task(data)
            elif data.type == "result":
                print(data.data)
        except socket.error:
            break

def send_message(server):
    while True:
        input("Press Enter to send a message to the server... \n")
        message = json.dumps({
            "client_id": ID,
            "type": "task", # execute, result
            "data": "Hello from client"
        })
        # server.send(message.encode('utf-8'))
        send_message(server, message)


def main():    
    server.connect((SERVER_IP, 9999))
    # print(socket.getaddrinfo(SERVER_IP, 9999))

    recieve_thread = threading.Thread(target=recieve_message, args=(server,))
    recieve_thread.start()

    send_thread = threading.Thread(target=send_message, args=(server,))
    send_thread.start()


if __name__ == '__main__':
    main()