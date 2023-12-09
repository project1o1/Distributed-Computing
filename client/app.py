from client import Commander, Soldier
import hashlib
import time

IP = '127.0.0.1'
PORT = 5000
ID = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()

def main():
    type = input("Enter type (commander C/soldier S): ").lower()
    if type == "c":
        client = Commander(IP, PORT, ID)
        while True:
            command = input("Enter command: ")
            result = client.command(command)
            print(f'Result: {result}')
    elif type == "s":
        client = Soldier(IP, PORT, ID)
        while True:
            print("Waiting for orders...")
            task_id = client.receive_orders()
            print(f'Obeyed order: {task_id}')


if __name__ == "__main__":
    main()