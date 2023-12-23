import logging
from models.TCPConnection import TCPConnection

VALID_VIDEO_EXTENSIONS = ('.mp4',)


class Client(TCPConnection):
    MAX_FILE_SIZE = 2 ** 47
    OUTPUT_FILE_NAME = 'output'

    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.sock.settimeout(Client.TIMEOUT)

    def run(self):
        self.sock.connect((self.host, self.port))

    def process_video(self, params: dict):
        file_name = params['file_name']
        if not file_name.endswith(VALID_VIDEO_EXTENSIONS):
            logging.error(f'Invalid file extension: {file_name}')
            self.sock.close()
            return
        Client.send_header(self.sock, params['media_type'], params['request'], file_name)
        Client.send_body(self.sock, params['media_type'], params['request'], file_name)
        logging.info('Waiting for response...')
        request_size, media_type_size, payload_size = Client.receive_header(self.sock)
        logging.info(f'request_size: {request_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
        Client.receive_body(self.sock, request_size, media_type_size, payload_size)