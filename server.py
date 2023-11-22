import socket


class Server:
    def __init__(self):
        self.host = 'localhost'
        self.port = 8080
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f'Listening on port {self.port}')

    def listen(self):
        while True:
            conn, addr = self.socket.accept()
            print(f'Connected by {addr}')
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)
            conn.close()

    def close(self):
        self.socket.close()


def main():
    server = Server()
    try:
        server.listen()
    except KeyboardInterrupt:
        server.close()


if __name__ == '__main__':
    main()