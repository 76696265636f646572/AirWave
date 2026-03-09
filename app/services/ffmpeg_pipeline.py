from __future__ import annotations

import subprocess
from typing import IO


class FfmpegError(RuntimeError):
    pass


class FfmpegPipeline:
    def __init__(self, ffmpeg_path: str, bitrate: str = "128k") -> None:
        self.ffmpeg_path = ffmpeg_path
        self.bitrate = bitrate

    def _spawn(self, args: list[str]) -> subprocess.Popen[bytes]:
        try:
            return subprocess.Popen(
                [self.ffmpeg_path, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise FfmpegError(
                f"ffmpeg binary not found at '{self.ffmpeg_path}'. "
                "Install ffmpeg or set MYTUBE_FFMPEG_PATH."
            ) from exc

    def spawn_for_source(self, source_url: str) -> subprocess.Popen[bytes]:
        args = [
            "-re",
            "-i",
            source_url,
            "-vn",
            "-acodec",
            "libmp3lame",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-b:a",
            self.bitrate,
            "-f",
            "mp3",
            "pipe:1",
        ]
        return self._spawn(args)

    def spawn_silence(self) -> subprocess.Popen[bytes]:
        args = [
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-acodec",
            "libmp3lame",
            "-b:a",
            self.bitrate,
            "-f",
            "mp3",
            "pipe:1",
        ]
        return self._spawn(args)

    @staticmethod
    def read_chunk(stdout: IO[bytes] | None, chunk_size: int) -> bytes:
        if stdout is None:
            return b""
        return stdout.read(chunk_size)
