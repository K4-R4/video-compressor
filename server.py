import os.path
import socket
import struct
import threading


class Server:
    buffer_size = 1400
    header_size = 32
    response_size = 16
    dest_dir = './dest/'

    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        # プログラム終了時にソケットを閉じる
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                threading.Thread(target=Server.listen_to_client, args=(client, address)).start()
        except KeyboardInterrupt as e:
            print(e)
        finally:
            self.sock.close()

    # クライアントからのメッセージを待ち受ける
    @staticmethod
    def listen_to_client(client: socket.socket, address: tuple):
        file_size = Server.receive_header(client)
        if file_size == 0:
            return
        Server.receive_body(client, file_size)

    @staticmethod
    def receive_header(client: socket.socket) -> int:
        # 32バイトのヘッダーを受信する
        header = client.recv(32)
        try:
            file_size_bytes, = struct.unpack('32s', header)
            file_size = int.from_bytes(file_size_bytes, 'big')
            print('File size: ', file_size)
            return file_size
        except struct.error as e:
            print(e)
            client.close()
            return 0

    @staticmethod
    def receive_body(client: socket.socket, file_size: int):
        # クライアントから送られたデータをファイルに保存する
        parent_dir = os.path.dirname(Server.dest_dir)
        if not os.path.exists(parent_dir):
            os.mkdir(parent_dir)
        print(f'File will be saved to {parent_dir}')
        address, port = client.getsockname()
        with open(f'{parent_dir}/{address}_{port}.mp4', 'wb') as f:
            try:
                while file_size > 0:
                    data = client.recv(Server.buffer_size)
                    file_size -= len(data)
                # 受信が終わったらクライアントに終了を通知する
                print('File has been received!')
                Server.respond(client, 200)
                client.close()
            # socketが例外を発生させたら接続を切る
            except socket.error as e:
                print(e)
                client.close()
                return

    @staticmethod
    def respond(client: socket.socket, data: int):
        # クライアントにデータを送信する
        packed_data = struct.pack('16s', data.to_bytes(16, 'big'))
        client.send(packed_data)


def main():
    server = Server('localhost', 5000)
    server.run()


if __name__ == '__main__':
    main()
