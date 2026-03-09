from dataclasses import dataclass

from app.db.repository import Repository
from app.services.playlist_service import PlaylistService
from app.services.yt_dlp_service import PlaylistPreview, ResolvedTrack


@dataclass
class FakeYtDlp:
    playlist: bool = False

    def is_playlist_url(self, url: str) -> bool:
        return self.playlist

    def resolve_video(self, url: str) -> ResolvedTrack:
        return ResolvedTrack(
            source_url=url,
            normalized_url=url,
            title="one",
            channel="chan",
            duration_seconds=100,
            thumbnail_url=None,
            stream_url="http://example/audio",
        )

    def preview_playlist(self, url: str) -> PlaylistPreview:
        return PlaylistPreview(
            source_url=url,
            title="pl",
            channel="chan",
            entries=[
                {
                    "source_url": "https://youtube.com/watch?v=1",
                    "normalized_url": "https://youtube.com/watch?v=1",
                    "title": "t1",
                    "channel": "ch1",
                    "duration_seconds": 60,
                    "thumbnail_url": None,
                },
                {
                    "source_url": "https://youtube.com/watch?v=2",
                    "normalized_url": "https://youtube.com/watch?v=2",
                    "title": "t2",
                    "channel": "ch2",
                    "duration_seconds": 61,
                    "thumbnail_url": None,
                },
            ],
        )


def test_add_single_video(tmp_path):
    repo = Repository(f"sqlite+pysqlite:///{tmp_path}/playlist.db")
    repo.init_db()
    service = PlaylistService(repo, FakeYtDlp(playlist=False))

    result = service.add_url("https://youtube.com/watch?v=abc")
    assert result["type"] == "video"
    assert result["count"] == 1
    queue = repo.list_queue()
    assert len(queue) == 1
    assert queue[0].title == "one"


def test_import_playlist(tmp_path):
    repo = Repository(f"sqlite+pysqlite:///{tmp_path}/playlist2.db")
    repo.init_db()
    service = PlaylistService(repo, FakeYtDlp(playlist=True))

    result = service.add_url("https://youtube.com/playlist?list=x")
    assert result["type"] == "playlist"
    assert result["count"] == 2
    queue = repo.list_queue()
    assert len(queue) == 2
