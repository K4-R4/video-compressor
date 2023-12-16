import socket
import threading


class Server:
    buffer_size = 1400

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.sock.bind((self.host, self.port))

        self.sock.listen(5)

    def run(self):
        self.accept()

    # クライアントの接続を待ち受ける
    def accept(self):
        try:
            while True:
                client, address = self.sock.accept()
                print(f'Connection from {address} has been established!')
                client.settimeout(60)
                threading.Thread(target=self.listen_to_client, args=(client, address)).start()
        except KeyboardInterrupt as e:
            print(e)
        finally:
            self.sock.close()

    # クライアントからのメッセージを待ち受ける
    def listen_to_client(self, client, address):
        # クライアントから送られたデータをファイルに保存する
        with open(f'{address}.mp4', 'wb') as f:
            while True:
                try:
                    data = client.recv(self.buffer_size)
                    if data:
                        f.write(data)
                    else:
                        break
                # socketが例外を発生させたら接続を切る
                except socket.error:
                    client.close()


def main():
    server = Server('localhost', 5000)
    server.run()


if __name__ == '__main__':
    main()
