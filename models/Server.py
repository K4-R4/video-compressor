import logging
import os.path
import socket
from concurrent.futures.thread import ThreadPoolExecutor
from models.VideoProcessor import VideoProcessor
from models.TCPConnection import TCPConnection


class Server(TCPConnection):
    LISTEN_NUM = 5
    MAX_WORKERS = 10

    def __init__(self, host: str, port: int, logger: logging.Logger):
        super().__init__(host, port, logger)
        self.executor = ThreadPoolExecutor(max_workers=Server.MAX_WORKERS)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

        self.sock.listen(Server.LISTEN_NUM)

    def run(self):
        self.accept()

    # クライアントの接続を待ち受ける
    def accept(self):
        try:
            while True:
                client, address = self.sock.accept()
                self.logger.info(f'Connection from {address} has been established!')
                client.settimeout(Server.TIMEOUT)
                self.executor.submit(Server.listen_to_client, client)
        except KeyboardInterrupt as e:
            self.logger.error(e, exc_info=True)
            self.sock.close()
            self.executor.shutdown(wait=True)

    # クライアントからのメッセージを待ち受ける
    def listen_to_client(self, client: socket.socket):
        try:
            request, saved_file_name = self.receive_request(client)
            self.process_request(client, request, saved_file_name)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            self.send_response(client,
                               '',
                               dict(status=500, message=str(e)),
                               '')
        finally:
            client.close()
            self.logger.info('Connection has been closed!')

    def process_request(self, client: socket.socket, request: dict, saved_file_name: str):
        self.logger.info('Processing...')
        # ファイルのパスを取得する
        input_file_path = os.path.join(Server.DEST_DIR, saved_file_name)
        output_file_path = os.path.join(Server.DEST_DIR, f'processed_{saved_file_name}')

        # ファイルを処理する
        media_type = VideoProcessor.process(request, input_file_path, output_file_path)

        # レスポンスを送信する
        self.send_response(client,
                           media_type,
                           dict(status=200, message='OK'),
                           output_file_path)

        # ファイルを削除する
        self.logger.info(f'Deleting files: {input_file_path} {output_file_path}')
        os.remove(input_file_path)
        os.remove(output_file_path)

    def receive_request(self, client: socket.socket):
        request_size, media_type_size, payload_size = self.receive_header(client)
        self.logger.info(
            f'request_size: {request_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
        request, saved_file_name = self.receive_body(client, request_size, media_type_size, payload_size)
        self.logger.info(f'Request: {request}, file_name: {saved_file_name}')
        return request, saved_file_name

    def send_response(self, client: socket.socket, media_type: str, response: dict, file_path: str):
        self.send_header(client, media_type, response, file_path)
        self.send_body(client, media_type, response, file_path)
