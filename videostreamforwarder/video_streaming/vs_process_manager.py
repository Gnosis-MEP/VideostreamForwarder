#!/usr/bin/env python
import sys
import subprocess

from videostreamforwarder.conf import (
    FFMPEG_BIN,
    VIDEO_STREAMER_PIPE_SCRIPT,
    VIDEO_STREAMER_SCRIPT,
    OUPUT_MEDIA_SERVER_URL
)

class VSProcessManager():
    def __init__(self, parent_service, pipe_script, vs_script, ffmpeg,  media_server_url, query_id, fps, width, height, video_output_type):
        self.parent_service = parent_service
        self.pipe_script = pipe_script
        self.ffmpeg = ffmpeg
        self.vs_script = vs_script
        self.media_server_url = media_server_url
        self.query_id = query_id
        self.fps = fps
        self.width = width
        self.height = height
        self.video_output_type = video_output_type
        # self.vs_cmd = self.prepare_vs_script_cmd()
        # self.ffmpeg_cmd = self.prepare_ffmpeg_cmd()

    # def prepare_vs_script_cmd(self):
    #     command = [
    #         'python', self.vs_script,
    #         f'{self.query_id}'
    #     ]
    #     return command

    # def prepare_ffmpeg_cmd(self):
    #     command = [
    #         self.ffmpeg,
    #         '-f', 'rawvideo',
    #         '-r', f'{self.fps}',
    #         '-pixel_format', 'bgr24',
    #         '-video_size', f'{self.width}x{self.height}',
    #         '-i', '-',
    #         '-vf', 'format=yuv420p',
    #         '-c:v', 'libx264',
    #         '-g', '1',
    #         '-x264opts', '"keyint=1:min-keyint=1:no-scenecut"',
    #         '-an',  # maybe add '-sn',
    #         '-f', 'flv',
    #         f'{self.media_server_url}/{self.query_id}'
    #     ]
    #     return command

    def piped_commands(self):
        command = [
            self.pipe_script,
            f'{self.vs_script}',
            f'{self.ffmpeg}',
            f'{self.query_id}',
            f'{self.video_output_type}',
            f'{self.width}x{self.height}',
            f'{self.fps}',
            f'{self.media_server_url}',
        ]
        return command

    def open_subprocess_pipe(self, cmd):
        return subprocess.Popen(cmd)

    def isOpened(self):
        return self.subprocess.poll() is None

    def close(self):
        self.subprocess.kill()

    def run(self):
        cmd = self.piped_commands()
        self.subprocess = self.open_subprocess_pipe(self.piped_commands())

if __name__ == '__main__':
    query_id = sys.argv[1]
    fps = float(sys.argv[2])
    width = int(sys.argv[3])
    height = int(sys.argv[4])

    query_vs_m = VSProcessManager(
        None,
        VIDEO_STREAMER_PIPE_SCRIPT,
        VIDEO_STREAMER_SCRIPT,
        FFMPEG_BIN,
        OUPUT_MEDIA_SERVER_URL,
        query_id,
        fps,
        width,
        height
    )
    query_vs_m.run()
