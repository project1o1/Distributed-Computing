from server import General

def main():
    IP = '0.0.0.0'
    PORT = 5000
    general = General(IP, PORT)
    print(f'[INFO] Server started on {IP}:{PORT}')
    while True:
        general.socket.listen()
        general.accept_client()

if __name__ == "__main__":
    main()