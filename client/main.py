from dotenv import load_dotenv
import logging
import os.path
import tkinter as tk
from tkinter import filedialog
from models.Client import Client


def main():
    # 環境変数の読み込み
    load_dotenv()
    server_ip = os.getenv('SERVER_IP')
    server_port = os.getenv('SERVER_PORT')

    # ログの設定
    logging.basicConfig(level=logging.INFO)

    # ウィンドウの設定
    root = tk.Tk()
    root.title('Video Compressor')
    root.geometry('500x500')

    # クライアントの起動
    client = Client(server_ip, int(server_port))
    client.run()

    # メインフレームの設定
    setting_frame = tk.Frame(root)
    setting_frame.pack()

    # ファイルアップロード用のフレームを作成
    file_selector, get_file_path = create_file_selector()
    file_upload_frame = tk.Frame(setting_frame)
    file_upload_frame.pack()
    label = tk.Label(file_upload_frame, text='File Path:')
    button = tk.Button(file_upload_frame, text='Select File', command=lambda: file_selector(label))
    button.pack(side='left')
    label.pack(side='left')

    # 各オプションごとにframeを作成しdictに格納
    options = {
        'Compress': ['compress rate'],
        'Resize': ['width', 'height'],
        'Change Aspect Ratio': ['width', 'height'],
        'Extract Audio': [],
        'Convert to GIF': ['start second', 'end second']
    }
    detail_setting_frame = {
        option_name: tk.Frame(setting_frame) for option_name in options
    }
    detail_setting_entries = {}

    option = tk.StringVar()
    for option_name in options:
        tk.Radiobutton(detail_setting_frame[option_name], text=option_name, value=option_name, variable=option,
                       command=lambda: update_entries(option_name, detail_setting_entries)).pack(
            side='left')
        # 各オプションごとにパラメータを入力するEntryを作成
        detail_setting_entries[option_name] = []
        # 各オプションごとにframeをpack
        for param in options[option_name]:
            tk.Label(detail_setting_frame[option_name], text=param).pack(side='left')
            entry = tk.Entry(detail_setting_frame[option_name])
            entry.pack(side='left')
            entry.config(state='disabled')
            detail_setting_entries[option_name].append(entry)
        detail_setting_frame[option_name].pack()

    root.mainloop()


def update_entries(selected_option: str, entries_dict: dict):
    # まずすべてのエントリを無効にする
    for entries in entries_dict.values():
        for entry in entries:
            entry.config(state='disabled')

    # 選択されたオプションのエントリを有効にする
    for entry in entries_dict.get(selected_option, []):
        entry.config(state='normal')


def create_file_selector():
    file_path = None

    # ファイル選択ダイアログを表示し、選択したファイルのパスを表示する
    def select_file(label: tk.Label):
        nonlocal file_path
        file_path = filedialog.askopenfilename()
        label.config(text=file_path)
        logging.info(f'file_path: {file_path}')

    def get_file_path():
        return file_path

    return select_file, get_file_path


if __name__ == '__main__':
    main()
