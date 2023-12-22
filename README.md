# Video Compressor

## Table of Contents
1. [Description](#description)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Demo](#demo)
6. [Technical details](#technical-details)

## [Description](#description)

## [Features](#features)
1. 圧縮
2. 解像度変更
3. アスペクト比を変更
4. 音声に変換
5. 指定した時間範囲でGIFに変換

## [Installation](#installation)
```bash
$ git clone https://github.com/tkuramot/video-compressor
$ cd video-compressor
$ brew install ffmpeg
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## [Usage](#usage)
```bash
$ python3 server.py
$ python3 client.py
```

## [Demo](#demo)

## [Technical details](#technical-details)
###  protocol
header: 64 bytes
- JSON size: 16 bytes
- media type size: 1 byte
- payload size: 47 bytes

payload: arbitrary bytes
- JSON: 2^16 bytes at most
- medit type size: 1 ~ 4 bytes (mp4, mp3, json, avi, ...)
- payload size: 2^47 bytes at most

Request
```json
{
  // compress, resolutionChange, aspectRatioChange, audioExtract, gifConvert
  "operation": "compress",
  "params": {
    // required for compress
    "bitrate": "1000k",
    // required for aspectRatioChange
    "aspectRatio": "16:9",
    // required for resolutionChange 
    "resolution": "1280x720",
    // required for gifConvert
    "startSec": "12",
    "endSec": "25"
  }
}
```

Response
```json
{
  "status": 200,
  "message": "OK"
}
```