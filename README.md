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

## [Usage](#usage)

## [Demo](#demo)

## [Technical details](#technical-details)
### Client-Server protocol
header: 64 bytes
- JSON size: 16 bytes
- media type size: 1 byte
- payload size: 47 bytes

payload: arbitrary bytes
- JSON: 2^16 bytes at most
- medit type size: 1 ~ 4 bytes (mp4, mp3, json, avi, ...)
- payload size: 2^47 bytes at most

JSON format
```json
{
  "operation": "compress", // compress, resolution, aspect, audio, gif
  "range": {
    "start": 0,
    "duration": 0
  }
}
```