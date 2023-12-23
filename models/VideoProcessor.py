import ffmpeg
import logging


class VideoProcessor:
    COMPRESS = "compress"
    RESOLUTION = "resolutionChange"
    ASPECT_RATIO = "aspectRatioChange"
    AUDIO = "audioExtract"
    GIF = "gifConvert"

    @staticmethod
    # 変換後の拡張子を返す
    def process(request: dict, input_file_path: str, output_file_path: str) -> str:
        if request['operation'] == VideoProcessor.COMPRESS:
            VideoProcessor.compress(input_file_path, output_file_path, request['params']['compressRate'])
            return 'mp4'
        elif request['operation'] == VideoProcessor.RESOLUTION:
            VideoProcessor.change_resolution(input_file_path, output_file_path, request['params']['width'],
                                             request['params']['height'])
            return 'mp4'
        elif request['operation'] == VideoProcessor.ASPECT_RATIO:
            VideoProcessor.change_aspect_ratio(input_file_path, output_file_path, request['params']['aspectRatio'])
            return 'mp4'
        elif request['operation'] == VideoProcessor.AUDIO:
            output_file_path = output_file_path.replace('.mp4', '.mp3')
            VideoProcessor.change_audio(input_file_path, output_file_path)
            return 'mp3'
        elif request['operation'] == VideoProcessor.GIF:
            output_file_path = output_file_path.replace('.mp4', '.gif')
            VideoProcessor.convert_to_gif(input_file_path, output_file_path, request['params']['startSec'],
                                          request['params']['endSec'])
            return 'gif'
        else:
            raise Exception(f'Unknown request type: {request["type"]}')

    @staticmethod
    def compress(input_file: str, output_file: str, compression_rate: float):
        logging.info(f'Compressing {input_file} to {output_file} with compression rate {compression_rate}')
        probe = ffmpeg.probe(input_file, cmd="ffprobe")
        video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
        default_bitrate: int = int(video_info["bit_rate"])
        compressed_bitrate: int = int(default_bitrate * float(compression_rate))
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
