from __future__ import annotations

from app.db.repository import NewQueueItem, Repository
from app.services.yt_dlp_service import PlaylistPreview, YtDlpService


class PlaylistService:
    def __init__(self, repository: Repository, yt_dlp_service: YtDlpService) -> None:
        self.repository = repository
        self.yt_dlp_service = yt_dlp_service

    def add_url(self, url: str) -> dict:
        if self.yt_dlp_service.is_playlist_url(url):
            return self.import_playlist(url)
        resolved = self.yt_dlp_service.resolve_video(url)
        self.repository.enqueue_items(
            [
                NewQueueItem(
                    source_url=resolved.source_url,
                    normalized_url=resolved.normalized_url,
                    source_type="video",
                    title=resolved.title,
                    channel=resolved.channel,
                    duration_seconds=resolved.duration_seconds,
                    thumbnail_url=resolved.thumbnail_url,
                )
            ]
        )
        return {"type": "video", "count": 1, "title": resolved.title}

    def preview_playlist(self, url: str) -> PlaylistPreview:
        return self.yt_dlp_service.preview_playlist(url)

    def import_playlist(self, url: str) -> dict:
        preview = self.yt_dlp_service.preview_playlist(url)
        playlist = self.repository.create_or_update_playlist(
            source_url=preview.source_url,
            title=preview.title,
            channel=preview.channel,
            entry_count=len(preview.entries),
        )
        items = [
            NewQueueItem(
                source_url=entry["source_url"],
                normalized_url=entry["normalized_url"],
                source_type="playlist_item",
                title=entry.get("title"),
                channel=entry.get("channel"),
                duration_seconds=entry.get("duration_seconds"),
                thumbnail_url=entry.get("thumbnail_url"),
                playlist_id=playlist.id,
            )
            for entry in preview.entries
        ]
        self.repository.enqueue_items(items)
        return {"type": "playlist", "count": len(items), "title": preview.title}
