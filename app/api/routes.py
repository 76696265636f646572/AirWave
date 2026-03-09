from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

from app.services.stream_engine import StreamEngine

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class AddUrlRequest(BaseModel):
    url: HttpUrl


class ReorderRequest(BaseModel):
    new_position: int


class SonosPlayRequest(BaseModel):
    speaker_ip: str


def _services(request: Request) -> dict[str, Any]:
    return {
        "repo": request.app.state.repository,
        "playlist": request.app.state.playlist_service,
        "engine": request.app.state.stream_engine,
        "settings": request.app.state.settings,
        "sonos": request.app.state.sonos_service,
    }


def _stream_url(request: Request) -> str:
    return _services(request)["settings"].stream_url_for(str(request.base_url))


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    services = _services(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": services["settings"].app_name,
            "stream_url": _stream_url(request),
        },
    )


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    services = _services(request)
    return {"status": "ok", "mode": services["engine"].state.mode.value}


@router.get("/state")
def state(request: Request) -> dict[str, Any]:
    services = _services(request)
    engine: StreamEngine = services["engine"]
    return {
        "mode": engine.state.mode.value,
        "now_playing_id": engine.state.now_playing_id,
        "now_playing_title": engine.state.now_playing_title,
        "stream_url": _stream_url(request),
    }


@router.get("/queue")
def list_queue(request: Request) -> list[dict[str, Any]]:
    queue = _services(request)["repo"].list_queue()
    return [
        {
            "id": item.id,
            "title": item.title,
            "source_url": item.source_url,
            "status": item.status.value,
            "queue_position": item.queue_position,
            "source_type": item.source_type,
        }
        for item in queue
    ]


@router.post("/queue/add")
def add_to_queue(payload: AddUrlRequest, request: Request) -> dict[str, Any]:
    result = _services(request)["playlist"].add_url(str(payload.url))
    return {"ok": True, **result}


@router.post("/queue/{item_id}/reorder")
def reorder_queue(item_id: int, payload: ReorderRequest, request: Request) -> dict[str, bool]:
    ok = _services(request)["repo"].reorder_item(item_id=item_id, new_position=payload.new_position)
    if not ok:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return {"ok": True}


@router.delete("/queue/{item_id}")
def remove_queue_item(item_id: int, request: Request) -> dict[str, bool]:
    services = _services(request)
    item = services["repo"].get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Queue item not found")
    ok = services["repo"].remove_item(item_id=item_id)
    if item.status.value == "playing":
        services["engine"].skip_current()
    return {"ok": ok}


@router.post("/queue/skip")
def skip_current(request: Request) -> dict[str, bool]:
    _services(request)["engine"].skip_current()
    return {"ok": True}


@router.get("/history")
def history(request: Request) -> list[dict[str, Any]]:
    services = _services(request)
    rows = services["repo"].list_history(limit=services["settings"].history_limit)
    return [
        {
            "id": row.id,
            "queue_item_id": row.queue_item_id,
            "title": row.title,
            "source_url": row.source_url,
            "status": row.status,
            "started_at": row.started_at,
            "finished_at": row.finished_at,
            "error_message": row.error_message,
        }
        for row in rows
    ]


@router.post("/playlist/preview")
def playlist_preview(payload: AddUrlRequest, request: Request) -> dict[str, Any]:
    preview = _services(request)["playlist"].preview_playlist(str(payload.url))
    return {
        "source_url": preview.source_url,
        "title": preview.title,
        "channel": preview.channel,
        "entries": preview.entries,
        "count": len(preview.entries),
    }


@router.post("/playlist/import")
def playlist_import(payload: AddUrlRequest, request: Request) -> dict[str, Any]:
    result = _services(request)["playlist"].import_playlist(str(payload.url))
    return {"ok": True, **result}


@router.get("/stream/live.mp3")
def stream_live(request: Request) -> StreamingResponse:
    engine = _services(request)["engine"]
    return StreamingResponse(engine.subscribe(), media_type="audio/mpeg")


@router.get("/sonos/speakers")
def sonos_speakers(request: Request) -> list[dict[str, str]]:
    speakers = _services(request)["sonos"].discover_speakers()
    return [{"ip": speaker.ip, "name": speaker.name} for speaker in speakers]


@router.post("/sonos/play")
def sonos_play(payload: SonosPlayRequest, request: Request) -> dict[str, bool]:
    services = _services(request)
    services["sonos"].play_stream(payload.speaker_ip, _stream_url(request))
    return {"ok": True}
