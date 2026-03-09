from io import BytesIO

from app.db.models import QueueStatus
from app.db.repository import NewQueueItem, Repository
from app.services.stream_engine import PlaybackMode, SharedMp3Hub, StreamEngine
from app.services.yt_dlp_service import ResolvedTrack


class FakeProc:
    def __init__(self, payload: bytes) -> None:
        self.stdout = BytesIO(payload)

    def terminate(self) -> None:
        return

    def wait(self, timeout: float | None = None) -> None:
        return


class FakeFfmpeg:
    def spawn_for_source(self, source_url: str) -> FakeProc:
        _ = source_url
        return FakeProc(b"abc123")

    def spawn_silence(self) -> FakeProc:
        return FakeProc(b"\x00" * 8)

    @staticmethod
    def read_chunk(stdout, chunk_size: int) -> bytes:
        return stdout.read(chunk_size)


class FakeYtDlp:
    def resolve_video(self, url: str) -> ResolvedTrack:
        return ResolvedTrack(
            source_url=url,
            normalized_url=url,
            title="resolved",
            channel="chan",
            duration_seconds=120,
            thumbnail_url=None,
            stream_url="http://media.local/audio",
        )


def test_shared_hub_fan_out():
    hub = SharedMp3Hub()
    gen1 = hub.subscribe()
    gen2 = hub.subscribe()
    hub.publish(b"chunk")
    assert next(gen1) == b"chunk"
    assert next(gen2) == b"chunk"


def test_stream_engine_playback_lifecycle(tmp_path):
    repo = Repository(f"sqlite+pysqlite:///{tmp_path}/engine.db")
    repo.init_db()
    created = repo.enqueue_items(
        [NewQueueItem(source_url="u", normalized_url="u", source_type="video", title="Song")]
    )
    item = repo.dequeue_next()
    assert item is not None

    engine = StreamEngine(
        repository=repo,
        yt_dlp_service=FakeYtDlp(),
        ffmpeg_pipeline=FakeFfmpeg(),
        chunk_size=2,
        queue_poll_seconds=0.1,
    )
    engine._play_item(created[0].id)  # noqa: SLF001 - lifecycle unit coverage
    assert engine.state.mode == PlaybackMode.playing

    finished = repo.get_item(created[0].id)
    assert finished is not None
    assert finished.status in (QueueStatus.completed, QueueStatus.skipped)
