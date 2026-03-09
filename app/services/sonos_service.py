from __future__ import annotations

from dataclasses import dataclass

try:
    from soco import SoCo, discover
except Exception:  # pragma: no cover - optional runtime dependency
    SoCo = None
    discover = None


@dataclass
class SonosSpeaker:
    ip: str
    name: str


class SonosService:
    def discover_speakers(self, timeout: int = 2) -> list[SonosSpeaker]:
        if discover is None:
            return []
        speakers = discover(timeout=timeout) or set()
        return [SonosSpeaker(ip=speaker.ip_address, name=speaker.player_name) for speaker in speakers]

    def play_stream(self, speaker_ip: str, stream_url: str) -> None:
        if SoCo is None:
            raise RuntimeError("SoCo not installed")
        speaker = SoCo(speaker_ip)
        speaker.play_uri(stream_url, title="MyTube Radio")
