from __future__ import annotations

import json
import subprocess
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.services.resolver.base import PlaylistPreview, ResolvedTrack, ResolverError, SourceResolver
from app.services.resolver.utils import is_youtube_url, source_site_from_url


class YtDlpError(ResolverError):
    pass


SEARCH_PREFIXES = {
    "youtube": "ytsearch",
    "soundcloud": "scsearch",
    "vimeo": "vimsearch",
}

GENERIC_COLLECTION_KEYWORDS = (
    "playlist",
    "playlists",
    "album",
    "albums",
    "channel",
    "channels",
    "artist",
    "artists",
    "collection",
    "collections",
    "show",
    "shows",
    "podcast",
    "podcasts",
    "likes",
    "tracks",
    "videos",
    "uploads",
    "sets",
    "set",
    "tag",
    "tags",
    "music",
)


class YtDlpResolver(SourceResolver):
    def __init__(
        self,
        binary_path: str,
        *,
        blocked_domains: list[str] | None = None,
        blocked_extractors: list[str] | None = None,
    ) -> None:
        self.binary_path = binary_path
        self.blocked_domains = [d.lower().strip() for d in (blocked_domains or []) if d.strip()]
        self.blocked_extractors = [e.lower().strip() for e in (blocked_extractors or []) if e.strip()]

    def _host(self, url: str) -> str:
        host = (urlparse(url).hostname or "").lower()
        if host.startswith("www."):
            return host[4:]
        return host

    def _looks_like_collection_url(self, url: str) -> bool:
        parsed = urlparse(url)
        host = self._host(url)
        path = (parsed.path or "").lower()
        query = parse_qs(parsed.query or "")

        # Preserve existing behavior: YouTube watch pages always represent a single video.
        if is_youtube_url(url):
            if "watch" in path:
                return False
            if "/playlist" in path and "list" in query:
                return True
            if path.startswith("/@") and path.count("/") >= 1:
                return True
            if path.startswith(("/channel/", "/c/", "/user/")):
                return True
            segments = [segment for segment in path.split("/") if segment]
            if len(segments) == 1 and segments[0] not in {"watch", "playlist", "results", "feed", "shorts", "live"}:
                return True

        if host.endswith("vimeo.com") and (path.startswith("/showcase/") or path.startswith("/channels/")):
            return True
        if host.endswith("dailymotion.com") and path.startswith("/playlist/"):
            return True
        if host.endswith("bilibili.com") and (
            path.startswith("/bangumi/play/ss")
            or "/channel/collectiondetail" in path
            or "sid" in query
        ):
            return True
        if host.endswith("soundcloud.com") and (
            "/sets/" in path
            or path.endswith("/tracks")
            or path.endswith("/likes")
            or path.count("/") == 2
        ):
            return True
        if host.endswith("bandcamp.com") and (path.startswith("/album/") or path.startswith("/music")):
            return True
        if host.endswith("audiomack.com") and ("/album/" in path or "/playlist/" in path):
            return True
        if host.endswith("mixcloud.com") and ("/playlists/" in path or path.startswith("/tag/")):
            return True
        if host.endswith("hearthis.at") and ("/set/" in path or path.count("/") == 2):
            return True
        if host.endswith("boomplay.com") and (path.startswith("/albums/") or path.startswith("/playlists/")):
            return True
        if host.endswith("anghami.com") and (path.startswith("/playlist/") or path.startswith("/album/")):
            return True
        if host.endswith("jamendo.com") and (path.startswith("/album/") or path.startswith("/artist/")):
            return True
        if host.endswith("archive.org") and path.startswith("/details/"):
            return True
        if host.endswith("freemusicarchive.org") and (path.startswith("/music/") or path.startswith("/curator/")):
            return True
        if host.endswith("house-mixes.com") and ("/profile/" in path):
            return True
        if host.endswith("1001tracklists.com") and (path.startswith("/tracklist/") or path.startswith("/dj/")):
            return True
        if host.endswith("nts.live") and path.startswith("/shows/"):
            return True
        if host.endswith("podcasts.apple.com") and "/podcast/" in path:
            return True
        if host.endswith("tunein.com") and path.startswith("/podcasts/"):
            return True
        if host.endswith("podbean.com"):
            return True
        if host.endswith("spreaker.com") and path.startswith("/show/"):
            return True
        if host.endswith("tiktok.com") and ("/@".lower() in path and ("/playlist/" in path or path.count("/") == 2)):
            return True
        if host.endswith("twitch.tv") and path.endswith("/videos"):
            return True
        if host.endswith("facebook.com") and path.endswith("/videos"):
            return True

        segments = [segment for segment in path.split("/") if segment]
        return any(segment in GENERIC_COLLECTION_KEYWORDS for segment in segments)

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc.endswith("youtu.be"):
            video_id = parsed.path.lstrip("/")
            return f"https://www.youtube.com/watch?v={video_id}"
        if "youtube.com" in parsed.netloc:
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
            playlist_id = query.get("list", [None])[0]
            if playlist_id:
                return f"https://www.youtube.com/playlist?list={playlist_id}"
        return url

    def _run_json(self, *args: str) -> dict[str, Any]:
        cmd = [self.binary_path, *args]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise YtDlpError(completed.stderr.strip() or "yt-dlp failed")
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise YtDlpError("Invalid JSON from yt-dlp") from exc

    def _ensure_domain_allowed(self, url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            return
        for blocked in self.blocked_domains:
            if host == blocked or host.endswith(f".{blocked}"):
                raise YtDlpError("This site is not allowed")

    def _extract_entry_url(self, entry: dict[str, Any]) -> str | None:
        webpage_url = entry.get("webpage_url")
        if isinstance(webpage_url, str) and webpage_url.startswith("http"):
            return webpage_url
        original_url = entry.get("original_url")
        if isinstance(original_url, str) and original_url.startswith("http"):
            return original_url
        raw_url = entry.get("url")
        if isinstance(raw_url, str) and raw_url.startswith("http"):
            return raw_url
        if isinstance(raw_url, str) and raw_url.startswith("//"):
            return f"https:{raw_url}"
        video_id = entry.get("id")
        extractor = (entry.get("extractor") or entry.get("extractor_key") or "").lower()
        if video_id and ("youtube" in extractor):
            return f"https://www.youtube.com/watch?v={video_id}"
        return None

    @staticmethod
    def _duration_seconds(value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return max(0, int(value))
        if isinstance(value, str):
            try:
                return max(0, int(float(value.strip())))
            except ValueError:
                return None
        return None

    def is_playlist_url(self, url: str) -> bool:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        parsed = urlparse(normalized)
        if is_youtube_url(normalized) and "watch" in (parsed.path or "").lower():
            return False
        if self._looks_like_collection_url(normalized):
            return True
        data = self._run_json("--flat-playlist", "--skip-download", "-J", normalized)
        entries = data.get("entries")
        if not isinstance(entries, list) or not entries:
            return False
        if data.get("_type") == "playlist":
            return True
        return len(entries) > 1

    def spawn_audio_stream(self, url: str) -> subprocess.Popen[bytes]:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        cmd = [
            self.binary_path,
            "--no-playlist",
            "-f",
            "bestaudio/best",
            "--no-progress",
            "--quiet",
            "-o",
            "-",
            normalized,
        ]
        try:
            return subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise YtDlpError(
                f"yt-dlp binary not found at '{self.binary_path}'. "
                "Install yt-dlp or set MYTUBE_YT_DLP_PATH."
            ) from exc

    def resolve_video(self, url: str) -> ResolvedTrack:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        data = self._run_json("--no-playlist", "-f", "bestaudio/best", "--skip-download", "-J", normalized)
        direct_url = data.get("url")
        if not direct_url:
            raise YtDlpError("Could not resolve direct stream URL")
        is_live = bool(data.get("is_live")) or str(data.get("live_status") or "").lower() in {"is_live", "post_live"}
        duration = self._duration_seconds(data.get("duration"))
        return ResolvedTrack(
            source_url=url,
            normalized_url=normalized,
            title=data.get("title"),
            channel=data.get("uploader") or data.get("channel"),
            duration_seconds=duration,
            thumbnail_url=data.get("thumbnail"),
            stream_url=direct_url,
            source_site=source_site_from_url(normalized),
            is_live=is_live,
            can_seek=bool((duration or 0) > 0 and not is_live),
        )

    def preview_playlist(self, url: str) -> PlaylistPreview:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        data = self._run_json("--flat-playlist", "--skip-download", "-J", normalized)
        entries: list[dict[str, Any]] = []
        for entry in data.get("entries", []):
            if not isinstance(entry, dict):
                continue
            source_url = self._extract_entry_url(entry)
            if not source_url:
                continue
            duration = self._duration_seconds(entry.get("duration"))
            entries.append(
                {
                    "source_url": source_url,
                    "normalized_url": source_url,
                    "title": entry.get("title"),
                    "channel": entry.get("uploader") or entry.get("channel"),
                    "duration_seconds": duration,
                    "thumbnail_url": entry.get("thumbnail"),
                    "source_site": source_site_from_url(source_url),
                    "is_live": bool(entry.get("is_live")),
                }
            )
        return PlaylistPreview(
            source_url=normalized,
            title=data.get("title"),
            channel=data.get("uploader") or data.get("channel"),
            entries=entries,
            thumbnail_url=data.get("thumbnail"),
        )

    def search(self, query: str, site: str = "youtube", limit: int = 10) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 25))
        site_key = (site or "youtube").strip().lower()
        prefix = SEARCH_PREFIXES.get(site_key, SEARCH_PREFIXES["youtube"])
        payload = self._run_json("--flat-playlist", "--skip-download", "-J", f"{prefix}{bounded_limit}:{query}")
        results: list[dict[str, Any]] = []
        for entry in payload.get("entries", []):
            if not isinstance(entry, dict):
                continue
            source_url = self._extract_entry_url(entry)
            if not source_url:
                continue
            duration = self._duration_seconds(entry.get("duration"))
            results.append(
                {
                    "id": entry.get("id") or source_url,
                    "source_url": source_url,
                    "normalized_url": source_url,
                    "title": entry.get("title"),
                    "channel": entry.get("uploader") or entry.get("channel"),
                    "duration_seconds": duration,
                    "thumbnail_url": entry.get("thumbnail"),
                    "source_site": source_site_from_url(source_url) or site_key.capitalize(),
                    "site": site_key,
                }
            )
        return results

