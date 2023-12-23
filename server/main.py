from dotenv import load_dotenv
import logging
import os
import sys
from models.Server import Server


def main():
    # 環境変数を読み込む
    load_dotenv()
    server_ip = os.getenv('SERVER_IP')
    server_port = os.getenv('SERVER_PORT')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # 情報（INFO）レベルのログを標準出力に出力するハンドラー
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    logger.addHandler(stdout_handler)

    # 警告（WARNING）以上のログを標準エラー出力に出力するハンドラー
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    logger.addHandler(stderr_handler)

    # サーバーを起動する
    server = Server(server_ip, int(server_port), logger)
    server.run()


if __name__ == '__main__':
    main()
