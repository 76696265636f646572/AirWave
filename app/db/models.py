from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class QueueStatus(str, Enum):
    queued = "queued"
    playing = "playing"
    completed = "completed"
    failed = "failed"
    removed = "removed"
    skipped = "skipped"


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    queue_items: Mapped[list["QueueItem"]] = relationship(back_populates="playlist")


class QueueItem(Base):
    __tablename__ = "queue_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="video")
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[QueueStatus] = mapped_column(SqlEnum(QueueStatus), nullable=False, default=QueueStatus.queued)
    queue_position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    resolved_stream_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    playlist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("playlists.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    playlist: Mapped[Optional[Playlist]] = relationship(back_populates="queue_items")
    history_entries: Mapped[list["PlayHistory"]] = relationship(back_populates="queue_item")


class PlayHistory(Base):
    __tablename__ = "play_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    queue_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("queue_items.id"), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    queue_item: Mapped[Optional[QueueItem]] = relationship(back_populates="history_entries")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
