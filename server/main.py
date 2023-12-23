from dotenv import load_dotenv
import logging
import os
from models.Server import Server


def main():
    # 環境変数を読み込む
    load_dotenv()
    server_ip = os.getenv('SERVER_IP')
    server_port = os.getenv('SERVER_PORT')

    # サーバーを起動する
    server = Server(server_ip, int(server_port), logging.getLogger())
    server.run()


if __name__ == '__main__':
    main()
