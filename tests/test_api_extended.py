from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@dataclass
class FakePlaylistService:
    def add_url(self, url: str) -> dict:
        return {"type": "video", "count": 1, "title": f"added:{url}"}

    def preview_playlist(self, url: str):
        return SimpleNamespace(source_url=url, title="preview", channel="chan", entries=[{"id": "1"}, {"id": "2"}])

    def import_playlist(self, url: str) -> dict:
        return {"type": "playlist", "count": 2, "title": f"imported:{url}"}


@dataclass
class FakeEngine:
    def __post_init__(self):
        self.state = SimpleNamespace(mode=SimpleNamespace(value="idle"), now_playing_id=None, now_playing_title=None)
        self.skipped = False

    def skip_current(self) -> None:
        self.skipped = True

    def subscribe(self):
        def _gen():
            yield b"chunk-1"
            yield b"chunk-2"

        return _gen()


@dataclass
class FakeSonosService:
    def discover_speakers(self, timeout: int = 2):
        _ = timeout
        return [SimpleNamespace(ip="192.168.1.10", name="Living Room")]

    def play_stream(self, speaker_ip: str, stream_url: str) -> None:
        self.last_play = (speaker_ip, stream_url)


def _build_test_client(tmp_path):
    settings = Settings(
        db_url=f"sqlite+pysqlite:///{tmp_path}/extended.db",
        yt_dlp_path="/bin/echo",
        ffmpeg_path="/bin/echo",
    )
    app = create_app(settings=settings, start_engine=False)
    client = TestClient(app)
    return client, app


def test_browser_root_and_static_assets(tmp_path):
    client, _app = _build_test_client(tmp_path)
    with client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Shared stream" in resp.text

        css = client.get("/static/css/styles.css")
        assert css.status_code == 200
        assert "background" in css.text

        js = client.get("/static/js/app.js")
        assert js.status_code == 200
        assert "refreshAll" in js.text


def test_queue_playlist_and_history_endpoints(tmp_path):
    client, app = _build_test_client(tmp_path)
    with client:
        app.state.playlist_service = FakePlaylistService()
        app.state.stream_engine = FakeEngine()

        add = client.post("/queue/add", json={"url": "https://www.youtube.com/watch?v=abc"})
        assert add.status_code == 200
        assert add.json()["ok"] is True

        preview = client.post("/playlist/preview", json={"url": "https://www.youtube.com/playlist?list=pl"})
        assert preview.status_code == 200
        assert preview.json()["count"] == 2

        imported = client.post("/playlist/import", json={"url": "https://www.youtube.com/playlist?list=pl"})
        assert imported.status_code == 200
        assert imported.json()["ok"] is True

        queue_resp = client.get("/queue")
        assert queue_resp.status_code == 200
        assert isinstance(queue_resp.json(), list)

        history_resp = client.get("/history")
        assert history_resp.status_code == 200
        assert isinstance(history_resp.json(), list)


def test_stream_endpoint_returns_bytes_without_hanging(tmp_path):
    client, app = _build_test_client(tmp_path)
    with client:
        app.state.stream_engine = FakeEngine()
        with client.stream("GET", "/stream/live.mp3") as resp:
            assert resp.status_code == 200
            iterator = resp.iter_bytes()
            first = next(iterator)
            assert first.startswith(b"chunk-")


def test_sonos_endpoints(tmp_path):
    client, app = _build_test_client(tmp_path)
    with client:
        fake_sonos = FakeSonosService()
        app.state.sonos_service = fake_sonos

        speakers = client.get("/sonos/speakers")
        assert speakers.status_code == 200
        payload = speakers.json()
        assert len(payload) == 1
        assert payload[0]["name"] == "Living Room"

        play = client.post("/sonos/play", json={"speaker_ip": "192.168.1.10"})
        assert play.status_code == 200
        assert play.json()["ok"] is True
        assert fake_sonos.last_play[0] == "192.168.1.10"
        assert fake_sonos.last_play[1].endswith("/stream/live.mp3")
