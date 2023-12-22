import json
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
    BUFFER_SIZE = 1400
    MAX_FILE_SIZE = 2 ** 47
    HEADER_SIZE = 64
    HEADER_FORMAT = '16s1s47s'

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
        request = {
            "operation": "compress",
            "params": {
                "compress_rate": 0.5
            }
        }
        media_type = "mp4"
        self.send_header(file_name, media_type, request)
        self.send_body(file_name, media_type, request)
        resp = self.receive_status()
        print(f'Response from server: {resp}')

    def send_header(self, file_name: str, media_type: str, request: dict):
        request_size = len(bytes(json.dumps(request), 'utf-8'))
        media_type_size = len(bytes(media_type, 'utf-8'))
        payload_size = os.path.getsize(file_name)
        print(f'File size: {payload_size}')
        if payload_size > Client.MAX_FILE_SIZE:
            print('File size is too large!')
            self.sock.close()
            return
        packed_header = struct.pack(Client.HEADER_FORMAT,
                                    int.to_bytes(request_size, 16, 'big'),
                                    int.to_bytes(media_type_size, 1, 'big'),
                                    int.to_bytes(payload_size, 47, 'big'))
        self.sock.send(packed_header)

    def send_body(self, file_name: str, media_type: str, request: dict):
        # jsonを送信する
        json_data = json.dumps(request)
        self.sock.send(bytes(json_data, 'utf-8'))
        # media_typeを送信する
        self.sock.send(bytes(media_type, 'utf-8'))
        # ファイルを読み込んで送信する
        with open(file_name, 'rb') as f:
            try:
                # self.buffer_size分ずつファイルを読み込んで送信する
                while True:
                    data = f.read(self.BUFFER_SIZE)
                    if data:
                        self.sock.send(data)
                    else:
                        print('File has been sent!')
                        break
            # socketが例外を発生させたら接続を切る
            except socket.error:
                self.sock.close()

    def receive_status(self) -> int:
        json_size = self.fetch_response_size()
        # jsonを受信する
        request_bytes = self.sock.recv(json_size)
        request_string = request_bytes.decode('utf-8')
        # dictに変換する
        request = json.loads(request_string)
        return request

    def fetch_response_size(self) -> int:
        header = self.sock.recv(Client.HEADER_SIZE)
        try:
            json_size_bytes, _, _ = struct.unpack(Client.HEADER_FORMAT, header)
            json_size = int.from_bytes(json_size_bytes, 'big')
            return json_size
        except struct.error as e:
            print(e)
            self.sock.close()
            return 0


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
