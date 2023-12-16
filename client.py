import mimetypes
import os.path
import socket
import struct
import sys


class FileValidator:
    @staticmethod
    def is_mp4(file_name):
        mime_type, _ = mimetypes.guess_type(file_name)
        return mime_type == 'video/mp4'


class Client:
    buffer_size = 1400
    max_file_size = 2 ** 32
    header_size = 32
    response_size = 16

    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port

    def run(self, file_name: str):
        self.sock.connect((self.host, self.port))
        if not FileValidator.is_mp4(file_name):
            print('The file must be mp4 format')
            self.sock.close()
            return
        self.send_header(file_name)
        self.send_body(file_name)

    # ファイルサイズを32バイトで送信する
    # 2^32 = 4GBまでしか送信できない
    def send_header(self, file_name: str):
        file_size = os.path.getsize(file_name)
        print(f'File size: {file_size}')
        if file_size > Client.max_file_size:
            print('File size is too large!')
            self.sock.close()
            return
        # ファイルサイズを32バイトにするために空白で埋める
        packed_data = struct.pack('32s', file_size.to_bytes(32, 'big'))
        self.sock.send(packed_data)

    def send_body(self, file_name: str):
        with open(file_name, 'rb') as f:
            try:
                # self.buffer_size分ずつファイルを読み込んで送信する
                while True:
                    data = f.read(self.buffer_size)
                    if data:
                        self.sock.send(data)
                    else:
                        print('File has been sent!')
                        resp = self.receive_status()
                        print(f'Response from server: {resp}')
                        break
            # socketが例外を発生させたら接続を切る
            except socket.error:
                self.sock.close()

    def receive_status(self) -> int:
        # サーバーからのレスポンスを受け取る
        data = self.sock.recv(Client.response_size)
        status_code_bytes, = struct.unpack('16s', data)
        return int.from_bytes(status_code_bytes, 'big')


def main():
    client = Client('localhost', 5000)
    # 引数にファイル名を指定する
    if len(sys.argv) != 2:
        print('Usage: python client.py [file_name]')
        sys.exit(1)

    file_name = sys.argv[1]
    # ファイルが存在するか確認する
    if not os.path.exists(file_name):
        print(f'{sys.argv[1]} does not exist!')
        sys.exit(1)
    client.run(file_name)


if __name__ == '__main__':
    main()
