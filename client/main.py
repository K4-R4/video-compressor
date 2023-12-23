from dotenv import load_dotenv
import logging
import os.path
import tkinter as tk
from tkinter import filedialog
import tkinter.ttk as ttk
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
    setup_layout(root)

    # クライアントの起動
    client = Client(server_ip, int(server_port))
    client.run()

    # メインフレームの設定
    setting_frame = tk.Frame(root)
    setting_frame.pack(expand=True, fill='both', padx=20, pady=20)

    # ファイルアップロード用のフレームを作成
    file_selector, get_file_path = create_file_selector()
    file_path_label = create_labelled_button(setting_frame, 'File Path:', lambda: file_selector(file_path_label))

    # オプション設定
    option = tk.StringVar()
    options = {
        'Compress': ['compress rate'],
        'Resize': ['width', 'height'],
        'Change Aspect Ratio': ['width', 'height'],
        'Extract Audio': [],
        'Convert to GIF': ['start second', 'end second']
    }
    detail_option_entries = setup_options(setting_frame, options, option)

    # ボタンを作成
    button_frame = tk.Frame(root)
    button_frame.pack(fill='x', padx=20, pady=20)
    tk.Button(button_frame, text='Process',
              command=lambda: process_video(get_file_path(), option, detail_option_entries, client)).pack(side='right')

    root.mainloop()


def setup_layout(root):
    root.title('Video Compressor')
    root.geometry('600x400')


def create_labelled_button(parent, text, command):
    frame = tk.Frame(parent, pady=5)
    label = tk.ttk.Label(frame, text=text, style='TLabel')
    button = tk.Button(frame, text='Select', command=command)
    label.pack(side='left', padx=(0, 10))
    button.pack(side='right')
    frame.pack(fill='x', padx=20, pady=5)
    return label


def setup_options(parent, options, option_variable):
    entries_dict = {}
    for option_name, params in options.items():
        frame = tk.Frame(parent)
        tk.Radiobutton(frame, text=option_name, value=option_name, variable=option_variable,
                       command=lambda: update_entries(option_variable.get(), entries_dict)).pack(
            side='left', padx=5)
        entries = []
        for param in params:
            tk.Label(frame, text=param).pack(side='left', padx=5)
            entry = ttk.Entry(frame, style='TEntry')
            entry.pack(side='left', padx=5)
            entry.config(state='disabled')
            entries.append(entry)
        frame.pack(fill='x', padx=20, pady=5)
        entries_dict[option_name] = entries
    return entries_dict


def update_entries(selected_option, entries_dict):
    for entries in entries_dict.values():
        for entry in entries:
            entry.config(state='disabled')
    for entry in entries_dict.get(selected_option, []):
        entry.config(state='normal')


def create_file_selector():
    file_path = ''

    def select_file(label):
        nonlocal file_path
        file_path = filedialog.askopenfilename()
        label.config(text=file_path)
        logging.info(f'file_path: {file_path}')

    def get_file_path():
        return file_path

    return select_file, get_file_path


def process_video(file_path: str, option: tk.StringVar, detail_options: dict, client: Client):
    _, file_extension = os.path.splitext(file_path)
    # optionとoperationの対応
    operation = {
        'Compress': 'compress',
        'Resize': 'resolutionChange',
        'Change Aspect Ratio': 'aspectRatioChange',
        'Extract Audio': 'audioExtract',
        'Convert to GIF': 'logging'
    }

    params = {
        'file_name': file_path,
        'media_type': file_extension,
        'request': {
            'operation': operation[option.get()],
            'params': {
            }
        }
    }

    # 各オプションに対応するエントリーから値を取得し、それをリクエストの形式に合わせて辞書に格納
    if option.get() == 'Compress':
        params['request']['params']['compressRate'] = detail_options['Compress'][0].get()
    elif option.get() == 'Resize':
        params['request']['params']['resolution'] = detail_options['Resize'][0].get() + 'x' + detail_options['Resize'][
            1].get()
    elif option.get() == 'Change Aspect Ratio':
        params['request']['params']['aspectRatio'] = detail_options['Change Aspect Ratio'][0].get() + ':' + \
                                                     detail_options['Change Aspect Ratio'][1].get()
    elif option.get() == 'Extract Audio':
        pass
    elif option.get() == 'Convert to GIF':
        params['request']['params']['startSec'] = detail_options['Convert to GIF'][0].get()
        params['request']['params']['endSec'] = detail_options['Convert to GIF'][1].get()

    client.process_video(params)


if __name__ == '__main__':
    main()
