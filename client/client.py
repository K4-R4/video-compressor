import json
import logging
import os.path
import socket
import struct
import sys

VALID_VIDEO_EXTENSIONS = ('.mp4',)


class Client:
    BUFFER_SIZE = 1400
    MAX_FILE_SIZE = 2 ** 47
    HEADER_SIZE = 64
    HEADER_FORMAT = '16s1s47s'
    DEST_DIR = './dest'
    OUTPUT_FILE_NAME = 'output'

    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port

    def run(self, file_name: str):
        self.sock.connect((self.host, self.port))
        if not file_name.endswith(VALID_VIDEO_EXTENSIONS):
            logging.error(f'Invalid file extension: {file_name}')
            self.sock.close()
            return
        request = {
            "operation": "compress",
            "params": {
                "compressRate": 0.5
            }
        }
        media_type = "mp4"
        self.send_header(file_name, media_type, request)
        self.send_body(file_name, media_type, request)
        logging.info('Waiting for response...')
        json_size, media_type_size, payload_size = self.receive_header()
        logging.info(f'json_size: {json_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
        self.receive_body(json_size, media_type_size, payload_size)

    def send_header(self, file_path: str, media_type: str, request: dict):
        request_size = len(bytes(json.dumps(request), 'utf-8'))
        media_type_size = len(bytes(media_type, 'utf-8'))
        payload_size = os.path.getsize(file_path)
        logging.info(f'json_size: {request_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
        if payload_size > Client.MAX_FILE_SIZE:
            logging.error(f'File size is too big: {payload_size}')
            self.sock.close()
            return
        packed_header = struct.pack(Client.HEADER_FORMAT,
                                    int.to_bytes(request_size, 16, 'big'),
                                    int.to_bytes(media_type_size, 1, 'big'),
                                    int.to_bytes(payload_size, 47, 'big'))
        self.sock.send(packed_header)

    def send_body(self, file_path: str, media_type: str, request: dict):
        # jsonを送信する
        json_data = json.dumps(request)
        self.sock.send(bytes(json_data, 'utf-8'))
        # media_typeを送信する
        self.sock.send(bytes(media_type, 'utf-8'))
        # ファイルを読み込んで送信する
        with open(file_path, 'rb') as f:
            try:
                # self.buffer_size分ずつファイルを読み込んで送信する
                while True:
                    data = f.read(self.BUFFER_SIZE)
                    if data:
                        self.sock.send(data)
                    else:
                        logging.info('File has been sent!')
                        break
            # socketが例外を発生させたら接続を切る
            except socket.error:
                self.sock.close()

    def receive_header(self) -> tuple[int, int, int]:
        header = self.sock.recv(Client.HEADER_SIZE)
        json_size_bytes, media_type_size_bytes, payload_size_bytes = struct.unpack(Client.HEADER_FORMAT, header)
        json_size = int.from_bytes(json_size_bytes, 'big')
        media_type_size = int.from_bytes(media_type_size_bytes, 'big')
        payload_size = int.from_bytes(payload_size_bytes, 'big')
        return json_size, media_type_size, payload_size

    def receive_body(self, json_size: int, media_type_size: int, payload_size: int):
        # jsonを受信する
        request_bytes = self.sock.recv(json_size)
        request_string = request_bytes.decode('utf-8')
        # dictに変換する
        request = json.loads(request_string)

        if request['status'] != 200:
            logging.error(f'Error: {request["message"]}')
            return

        # メディアタイプを受信する
        media_type_bytes = self.sock.recv(media_type_size)
        media_type = media_type_bytes.decode('utf-8')

        # ファイルを受信する
        logging.info('Receiving file...')
        file_name = f'{Client.OUTPUT_FILE_NAME}.' + media_type
        file_path = os.path.join(Client.DEST_DIR, file_name)
        logging.info(f'Saving file to {file_path}')
        with open(file_path, 'wb') as f:
            while payload_size > 0:
                data = self.sock.recv(Client.BUFFER_SIZE)
                f.write(data)
                payload_size -= len(data)
            logging.info('File has been received!')


def main():
    logging.basicConfig(level=logging.INFO)
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
