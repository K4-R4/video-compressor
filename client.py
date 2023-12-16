import mimetypes
import socket
import sys


class FileValidator:
    @staticmethod
    def is_mp4(file_name):
        mime_type, _ = mimetypes.guess_type(file_name)
        return mime_type == 'video/mp4'


class Client:
    buffer_size = 1400

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port

    def run(self, file_name):
        self.sock.connect((self.host, self.port))
        if not FileValidator.is_mp4(file_name):
            print('The file must be mp4 format')
            return
        self.send_message(file_name)

    def send_message(self, file_name):
        with open(file_name, 'rb') as f:
            try:
                # self.buffer_size分ずつファイルを読み込んで送信する
                while True:
                    data = f.read(self.buffer_size)
                    if data:
                        self.sock.send(data)
                    else:
                        break
            # socketが例外を発生させたら接続を切る
            except socket.error:
                self.sock.close()


def main():
    client = Client('localhost', 5000)
    # 引数にファイル名を指定する
    if len(sys.argv) != 2:
        print('Usage: python client.py [file_name]')
        sys.exit(1)
    client.run(sys.argv[1])


if __name__ == '__main__':
    main()
