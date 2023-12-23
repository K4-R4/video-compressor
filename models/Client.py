import logging
from models.TCPConnection import TCPConnection

VALID_VIDEO_EXTENSIONS = ('.mp4',)


class Client(TCPConnection):
    MAX_FILE_SIZE = 2 ** 47
    OUTPUT_FILE_NAME = 'output'

    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.sock.settimeout(Client.TIMEOUT)

    def run(self, params: dict | None = None):
        self.sock.connect((self.host, self.port))
        file_name = params['file_name']
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
