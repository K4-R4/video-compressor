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
    DEST_DIR = './dest/'

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
            json_size, media_type_size, payload_size = Server.receive_header(client)
            logging.info(f'json_size: {json_size}, media_type_size: {media_type_size}, payload_size: {payload_size}')
            request, input_file = Server.receive_body(client, json_size, media_type_size, payload_size)
            logging.info(f'Request: {request}, file_name: {input_file}')
            logging.info('Processing...')
            output_file = VideoProcessor.process(request, input_file)
            logging.info(f'Delital file: {input_file} {output_file}')
            # ファイルを削除する
            os.remove(input_file)
            os.remove(output_file)
        except Exception as e:
            logging.error(e, exc_info=True)
            Server.respond(client, dict(status=500, message=str(e)))
        Server.respond(client, dict(status=200, message='OK'))

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
        parent_dir = os.path.dirname(Server.DEST_DIR)
        if not os.path.exists(parent_dir):
            os.mkdir(parent_dir)
        logging.info(f'File will be saved to {parent_dir}')
        address, port = client.getsockname()
        file_name = f'{parent_dir}/{address}_{port}.' + media_type
        with open(file_name, 'wb') as f:
            while payload_size > 0:
                data = client.recv(Server.BUFFER_SIZE)
                f.write(data)
                payload_size -= len(data)
            # 受信が終わったらクライアントに終了を通知する
            logging.info('File has been received!')
        return request, file_name

    @staticmethod
    def send_header(client: socket.socket, response: dict):
        request_size = len(bytes(json.dumps(response), 'utf-8'))
        packed_header = struct.pack(Server.HEADER_FORMAT,
                                    int.to_bytes(request_size, 16, 'big'),
                                    int.to_bytes(0, 1, 'big'),
                                    int.to_bytes(0, 47, 'big'))
        client.send(packed_header)

    @staticmethod
    def respond(client: socket.socket, response: dict):
        # データのサイズを送信する
        Server.send_header(client, response)
        # クライアントにデータを送信する
        response_bytes = bytes(json.dumps(response), 'utf-8')
        client.send(response_bytes)


class VideoProcessor:
    COMPRESS = "compress"
    RESOLUTION = "resolutionChange"
    ASPECT = "aspectChange"
    AUDIO = "audioExtract"
    GIF = "gifConvert"

    @staticmethod
    def process(request: dict, input_file: str) -> str:
        if request['operation'] == VideoProcessor.COMPRESS:
            output_file = f'compress_{input_file}'
            VideoProcessor.compress(input_file, output_file, request['params']['compressRate'])
            return output_file
        elif request['operation'] == VideoProcessor.RESOLUTION:
            output_file = f'resolution_{input_file}'
            VideoProcessor.change_resolution(input_file, output_file, request['params']['width'],
                                             request['params']['height'])
            return output_file
        elif request['operation'] == VideoProcessor.ASPECT:
            output_file = f'aspect_{input_file}'
            VideoProcessor.change_aspect_ratio(input_file, output_file, request['params']['aspectRatio'])
            return output_file
        elif request['operation'] == VideoProcessor.AUDIO:
            output_file = f'audio_{input_file}'
            VideoProcessor.change_audio(input_file, output_file)
            return output_file
        elif request['operation'] == VideoProcessor.GIF:
            output_file = f'gif_{input_file}'
            VideoProcessor.convert_to_gif(input_file, output_file, request['params']['startSec'],
                                          request['params']['endSec'])
            return output_file
        else:
            raise Exception(f'Unknown request type: {request["type"]}')

    @staticmethod
    def compress(input_file: str, output_file: str, compression_rate: float):
        logging.info(f'Compressing {input_file} to {output_file} with compression rate {compression_rate}')
        probe = ffmpeg.probe(input_file)
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
    logging.basicConfig(level=logging.INFO)
    server = Server('localhost', 5000)
    server.run()


if __name__ == '__main__':
    main()
