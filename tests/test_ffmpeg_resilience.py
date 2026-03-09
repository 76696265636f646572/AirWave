from __future__ import annotations

import time

from app.db.models import QueueStatus
from app.db.repository import NewQueueItem, Repository
from app.services.ffmpeg_pipeline import FfmpegError
from app.services.stream_engine import StreamEngine
from app.services.yt_dlp_service import ResolvedTrack


class MissingFfmpegPipeline:
    def spawn_silence(self):
        raise FfmpegError("ffmpeg missing")

    def spawn_for_source(self, source_url: str):
        _ = source_url
        raise FfmpegError("ffmpeg missing")

    @staticmethod
    def read_chunk(stdout, chunk_size: int):
        _ = stdout, chunk_size
        return b""


class FakeYtDlp:
    def resolve_video(self, url: str) -> ResolvedTrack:
        return ResolvedTrack(
            source_url=url,
            normalized_url=url,
            title="t",
            channel="c",
            duration_seconds=1,
            thumbnail_url=None,
            stream_url="http://x/audio",
        )


def test_engine_survives_missing_ffmpeg_in_idle(tmp_path):
    repo = Repository(f"sqlite+pysqlite:///{tmp_path}/idle.db")
    repo.init_db()
    engine = StreamEngine(
        repository=repo,
        yt_dlp_service=FakeYtDlp(),
        ffmpeg_pipeline=MissingFfmpegPipeline(),
        queue_poll_seconds=0.01,
    )
    engine.start()
    time.sleep(0.05)
    assert engine._worker is not None  # noqa: SLF001
    assert engine._worker.is_alive() is True  # noqa: SLF001
    engine.stop()


def test_engine_marks_track_failed_when_ffmpeg_missing(tmp_path):
    repo = Repository(f"sqlite+pysqlite:///{tmp_path}/play.db")
    repo.init_db()
    created = repo.enqueue_items(
        [NewQueueItem(source_url="u", normalized_url="u", source_type="video", title="song")]
    )
    item = repo.dequeue_next()
    assert item is not None

    engine = StreamEngine(
        repository=repo,
        yt_dlp_service=FakeYtDlp(),
        ffmpeg_pipeline=MissingFfmpegPipeline(),
        queue_poll_seconds=0.01,
    )
    engine._play_item(created[0].id)  # noqa: SLF001
    saved = repo.get_item(created[0].id)
    assert saved is not None
    assert saved.status == QueueStatus.failed
