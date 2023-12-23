from dotenv import load_dotenv
import logging
import os.path
import sys
from models.Client import Client


def main():
    load_dotenv()
    server_ip = os.getenv('SERVER_IP')
    server_port = os.getenv('SERVER_PORT')
    logging.basicConfig(level=logging.INFO)
    client = Client(server_ip, int(server_port))
    # 引数にファイル名を指定する
    if len(sys.argv) != 2:
        print('Usage: python Client.py [file_name]')
        sys.exit(1)

    file_name = sys.argv[1]
    # ファイルが存在するか確認する
    if not os.path.exists(file_name):
        print(f'{sys.argv[1]} does not exist!')
        sys.exit(1)
    client.run(dict(file_name=file_name))


if __name__ == '__main__':
    main()
