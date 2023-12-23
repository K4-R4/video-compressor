from dotenv import load_dotenv
import logging
import os.path
import sys
from models.TCPConnection import TCPConnection

VALID_VIDEO_EXTENSIONS = ('.mp4',)


class Client(TCPConnection):
    MAX_FILE_SIZE = 2 ** 47
    OUTPUT_FILE_NAME = 'output'

    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.sock.settimeout(60)

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
        Client.send_header(self.sock, file_name, media_type, request)
        Client.send_body(self.sock, file_name, media_type, request)
        logging.info('Waiting for response...')
        json_size, media_type_size, payload_size = Client.receive_header(self.sock)
        logging.info(f'json_size: {json_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
        Client.receive_body(self.sock, json_size, media_type_size, payload_size)


def main():
    load_dotenv()
    server_ip = os.getenv('SERVER_IP')
    server_port = os.getenv('SERVER_PORT')
    logging.basicConfig(level=logging.INFO)
    client = Client(server_ip, int(server_port))
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
