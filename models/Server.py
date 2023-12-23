import logging
import os.path
import socket
import threading
from models.VideoProcessor import VideoProcessor
from models.TCPConnection import TCPConnection


class Server(TCPConnection):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        # プログラム終了時にソケットを閉じる
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

        self.sock.listen(5)

    def run(self, params: dict | None = None):
        self.accept()

    # クライアントの接続を待ち受ける
    def accept(self):
        try:
            while True:
                client, address = self.sock.accept()
                logging.info(f'Connection from {address} has been established!')
                client.settimeout(Server.TIMEOUT)
                threading.Thread(target=Server.listen_to_client, args=(client,)).start()
        except KeyboardInterrupt as e:
            logging.error(e, exc_info=True)
        finally:
            self.sock.close()

    # クライアントからのメッセージを待ち受ける
    @staticmethod
    def listen_to_client(client: socket.socket):
        try:
            # ヘッダーを受信する
            json_size, media_type_size, payload_size = Server.receive_header(client)
            logging.info(f'json_size: {json_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
            request, input_file = Server.receive_body(client, json_size, media_type_size, payload_size)
            logging.info(f'Request: {request}, file_name: {input_file}')
            logging.info('Processing...')
            # ファイルのパスを取得する
            input_file_path = os.path.join(Server.DEST_DIR, input_file)
            output_file_path = os.path.join(Server.DEST_DIR, f'processed_{input_file}')
            # ファイルを処理する
            media_type = VideoProcessor.process(request, input_file_path, output_file_path)
            # レスポンスを送信する
            response = dict(status=200, message='OK')
            Server.send_header(client, output_file_path, media_type, response)
            Server.send_body(client, output_file_path, media_type, response)
            # ファイルを削除する
            logging.info(f'Deleting files: {input_file_path} {output_file_path}')
            os.remove(input_file_path)
            os.remove(output_file_path)
        except Exception as e:
            logging.error(e, exc_info=True)
            response = dict(status=500, message=str(e))
            Server.send_header(client, '', '', response)
            Server.send_body(client, '', '', response)
