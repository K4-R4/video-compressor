from dotenv import load_dotenv
import ffmpeg
import json
import logging
import os.path
import socket
import struct
import threading


class Server:
    BUFFER_SIZE = 1400
    HEADER_SIZE = 64
    HEADER_FORMAT = '16s1s47s'
    RESPONSE_SIZE = 16
    DEST_DIR = './dest'

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
                logging.info(f'Connection from {address} has been established!')
                client.settimeout(60)
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

    @staticmethod
    def receive_header(client: socket.socket) -> tuple[int, int, int]:
        header = client.recv(Server.HEADER_SIZE)
        json_size_bytes, media_type_size_bytes, payload_size_bytes = struct.unpack(Server.HEADER_FORMAT, header)
        json_size = int.from_bytes(json_size_bytes, 'big')
        media_type_size = int.from_bytes(media_type_size_bytes, 'big')
        payload_size = int.from_bytes(payload_size_bytes, 'big')
        return json_size, media_type_size, payload_size

    @staticmethod
    def receive_body(client: socket.socket, json_size: int, media_type_size: int, payload_size: int) -> tuple[
        dict, str,]:
        # jsonを受信する
        request_bytes = client.recv(json_size)
        request_string = request_bytes.decode('utf-8')
        # dictに変換する
        request = json.loads(request_string)

        # メディアタイプを受信する
        media_type_bytes = client.recv(media_type_size)
        media_type = media_type_bytes.decode('utf-8')

        # ファイルを受信する
        address, port = client.getsockname()
        file_name = f'{address}_{port}.' + media_type
        file_path = os.path.join(Server.DEST_DIR, file_name)
        logging.info(f'Saving file to {file_path}')
        with open(file_path, 'wb') as f:
            while payload_size > 0:
                data = client.recv(Server.BUFFER_SIZE)
                f.write(data)
                payload_size -= len(data)
            # 受信が終わったらクライアントに終了を通知する
            logging.info('File has been received!')
        return request, file_name

    @staticmethod
    def send_header(client: socket.socket, file_path: str, media_type: str, request: dict):
        request_size = len(bytes(json.dumps(request), 'utf-8'))
        media_type_size = len(bytes(media_type, 'utf-8'))
        payload_size = os.path.getsize(file_path)
        logging.info(f'json_size: {request_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
        packed_header = struct.pack(Server.HEADER_FORMAT,
                                    int.to_bytes(request_size, 16, 'big'),
                                    int.to_bytes(media_type_size, 1, 'big'),
                                    int.to_bytes(payload_size, 47, 'big'))
        client.send(packed_header)

    @staticmethod
    def send_body(client: socket.socket, file_path: str, media_type: str, request: dict):
        # jsonを送信する
        json_data = json.dumps(request)
        client.send(bytes(json_data, 'utf-8'))
        # media_typeを送信する
        client.send(bytes(media_type, 'utf-8'))
        # ファイルを読み込んで送信する
        with open(file_path, 'rb') as f:
            try:
                # self.buffer_size分ずつファイルを読み込んで送信する
                while True:
                    data = f.read(Server.BUFFER_SIZE)
                    if data:
                        client.send(data)
                    else:
                        logging.info('File has been sent!')
                        break
            # socketが例外を発生させたら接続を切る
            except socket.error:
                client.close()


class VideoProcessor:
    COMPRESS = "compress"
    RESOLUTION = "resolutionChange"
    ASPECT = "aspectChange"
    AUDIO = "audioExtract"
    GIF = "gifConvert"

    @staticmethod
    # 変換後の拡張子を返す
    def process(request: dict, input_file_path: str, output_file_path: str) -> str:
        if request['operation'] == VideoProcessor.COMPRESS:
            VideoProcessor.compress(input_file_path, output_file_path, request['params']['compressRate'])
            return 'mp4'
        elif request['operation'] == VideoProcessor.RESOLUTION:
            VideoProcessor.change_resolution(input_file_path, output_file_path, request['params']['width'],
                                             request['params']['height'])
            return 'mp4'
        elif request['operation'] == VideoProcessor.ASPECT:
            VideoProcessor.change_aspect_ratio(input_file_path, output_file_path, request['params']['aspectRatio'])
            return 'mp4'
        elif request['operation'] == VideoProcessor.AUDIO:
            output_file_path = output_file_path.replace('.mp4', '.mp3')
            VideoProcessor.change_audio(input_file_path, output_file_path)
            return 'mp3'
        elif request['operation'] == VideoProcessor.GIF:
            output_file_path = output_file_path.replace('.mp4', '.gif')
            VideoProcessor.convert_to_gif(input_file_path, output_file_path, request['params']['startSec'],
                                          request['params']['endSec'])
            return 'gif'
        else:
            raise Exception(f'Unknown request type: {request["type"]}')

    @staticmethod
    def compress(input_file: str, output_file: str, compression_rate: float):
        logging.info(f'Compressing {input_file} to {output_file} with compression rate {compression_rate}')
        probe = ffmpeg.probe(input_file, cmd="ffprobe")
        video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
        default_bitrate: int = int(video_info["bit_rate"])
        compressed_bitrate: int = int(default_bitrate * compression_rate)
        stream = ffmpeg.input(input_file).output(
            output_file, video_bitrate=compressed_bitrate
        )
        ffmpeg.run(stream, overwrite_output=True)

    @staticmethod
    def change_resolution(input_file: str, output_file: str, width: int, height: int):
        logging.info(f'Changing resolution of {input_file} to {output_file} with width {width} and height {height}')
        stream = ffmpeg.input(input_file)
        video = stream.filter("scale", width, height)
        audio = stream.audio
        ffmpeg.output(video, audio, output_file).run(overwrite_output=True)

    @staticmethod
    def change_aspect_ratio(input_file: str, output_file: str, aspect_ratio: str):
        logging.info(f'Changing aspect ratio of {input_file} to {output_file} with aspect ratio {aspect_ratio}')
        input_stream = ffmpeg.input(input_file)
        video = input_stream.filter("setdar", aspect_ratio)
        audio = input_stream.audio
        ffmpeg.output(video, audio, output_file).run(overwrite_output=True)

    @staticmethod
    def change_audio(input_file: str, output_file: str):
        logging.info(f'Changing audio of {input_file} to {output_file}')
        ffmpeg.input(input_file).output(output_file, format="mp3").run(overwrite_output=True)

    @staticmethod
    def convert_to_gif(input_file: str, output_file: str, start_sec: int, end_sec: int):
        logging.info(f'Converting {input_file} to {output_file} with start {start_sec} and end {end_sec}')
        stream = ffmpeg.input(input_file)
        video = stream.trim(start=start_sec, end=end_sec).setpts("PTS-STARTPTS")
        audio = stream.filter("atrim", start=start_sec, end=end_sec).filter(
            "asetpts", "PTS-STARTPTS"
        )
        ffmpeg.output(video, audio, output_file, format="gif").run()


def main():
    load_dotenv()
    server_ip = os.getenv('SERVER_IP')
    server_port = os.getenv('SERVER_PORT')
    logging.basicConfig(level=logging.INFO)
    server = Server(server_ip, int(server_port))
    server.run()


if __name__ == '__main__':
    main()
