import logging
from models.TCPConnection import TCPConnection

VALID_VIDEO_EXTENSIONS = ('.mp4',)


class Client(TCPConnection):
    MAX_FILE_SIZE = 2 ** 47
    OUTPUT_FILE_NAME = 'output'

    def __init__(self, host: str, port: int, logger: logging.Logger):
        super().__init__(host, port, logger)
        self.logger = logger
        self.sock.settimeout(Client.TIMEOUT)

    def run(self):
        self.sock.connect((self.host, self.port))

    def process_video(self, params: dict):
        file_name = params['file_name']
        if not file_name.endswith(VALID_VIDEO_EXTENSIONS):
            self.logger.error(f'Invalid file extension: {file_name}')
            self.sock.close()
            return
        self.send_header(self.sock, params['media_type'], params['request'], file_name)
        self.send_body(self.sock, params['media_type'], params['request'], file_name)
        self.logger.info('Waiting for response...')
        request_size, media_type_size, payload_size = self.receive_header(self.sock)
        self.logger.info(
            f'request_size: {request_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
        self.receive_body(self.sock, request_size, media_type_size, payload_size)
