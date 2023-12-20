import ffmpeg
import os.path
import socket
import struct
import threading


class Server:
    BUFFER_SIZE = 1400
    HEADER_SIZE = 32
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
                print(f'Connection from {address} has been established!')
                client.settimeout(60)
                threading.Thread(target=Server.listen_to_client, args=(client, address)).start()
        except KeyboardInterrupt as e:
            print(e)
        finally:
            self.sock.close()

    # クライアントからのメッセージを待ち受ける
    @staticmethod
    def listen_to_client(client: socket.socket, address: tuple):
        file_size = Server.receive_header(client)
        if file_size == 0:
            return
        Server.receive_body(client, file_size)

    @staticmethod
    def receive_header(client: socket.socket) -> int:
        # 32バイトのヘッダーを受信する
        header = client.recv(32)
        try:
            file_size_bytes, = struct.unpack('32s', header)
            file_size = int.from_bytes(file_size_bytes, 'big')
            print('File size: ', file_size)
            return file_size
        except struct.error as e:
            print(e)
            client.close()
            return 0

    @staticmethod
    def receive_body(client: socket.socket, file_size: int):
        # クライアントから送られたデータをファイルに保存する
        parent_dir = os.path.dirname(Server.DEST_DIR)
        if not os.path.exists(parent_dir):
            os.mkdir(parent_dir)
        print(f'File will be saved to {parent_dir}')
        address, port = client.getsockname()
        with open(f'{parent_dir}/{address}_{port}.mp4', 'wb') as f:
            try:
                while file_size > 0:
                    data = client.recv(Server.BUFFER_SIZE)
                    file_size -= len(data)
                # 受信が終わったらクライアントに終了を通知する
                print('File has been received!')
                Server.respond(client, 200)
                client.close()
            # socketが例外を発生させたら接続を切る
            except socket.error as e:
                print(e)
                client.close()
                return

    @staticmethod
    def respond(client: socket.socket, data: int):
        # クライアントにデータを送信する
        packed_data = struct.pack('16s', data.to_bytes(16, 'big'))
        client.send(packed_data)


class VideoProcessor:
    COMPRESS = "compress"
    RESOLUTION = "resolutionChange"
    ASPECT = "aspectChange"
    AUDIO = "audioExtract"
    GIF = "gifConvert"

    @staticmethod
    def compress(input_file: str, output_file: str, compression_rate: float):
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
        stream = ffmpeg.input(input_file)
        video = stream.filter("scale", width, height)
        audio = stream.audio
        ffmpeg.output(video, audio, output_file).run(overwrite_output=True)

    @staticmethod
    def change_aspect_ratio(input_file: str, output_file: str, aspect_ratio: str):
        input_stream = ffmpeg.input(input_file)
        video = input_stream.filter("setdar", aspect_ratio)
        audio = input_stream.audio
        ffmpeg.output(video, audio, output_file).run(overwrite_output=True)

    @staticmethod
    def change_audio(input_file: str, output_file: str):
        ffmpeg.input(input_file).output(output_file, format="mp3").run(overwrite_output=True)

    @staticmethod
    def convert_to_gif(input_file: str, output_file: str, start_sec: int, end_sec: int):
        stream = ffmpeg.input(input_file)
        video = stream.trim(start=start_sec, end=end_sec).setpts("PTS-STARTPTS")
        audio = stream.filter("atrim", start=start_sec, end=end_sec).filter(
            "asetpts", "PTS-STARTPTS"
        )
        ffmpeg.output(video, audio, output_file, format="gif").run()


def main():
    server = Server('localhost', 5000)
    server.run()


if __name__ == '__main__':
    main()
