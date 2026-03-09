# MyTube Radio

A WSL-friendly FastAPI application that exposes one shared live MP3 stream for all connected clients. Users can queue individual YouTube URLs or playlist URLs into a shared queue.

## Quick Start

1. Install Python 3.10+ and SQLite support.
2. Install dependencies:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `python -m pip install --upgrade pip setuptools wheel`
   - `python -m pip install ".[dev]"`
3. Install `yt-dlp` binary:
   - `./scripts/setup_yt_dlp.sh`
4. (Optional) install `ffmpeg` manually:
   - `./scripts/setup_ffmpeg.sh`
5. Start the app:
   - `./scripts/run_dev.sh`

Open `http://127.0.0.1:8000`.

If `ffmpeg` is missing, the app will try to auto-download a Linux binary from GitHub to `./bin/ffmpeg` at startup.

If the app is running in Docker or otherwise resolves to a non-routable local address for Sonos clients, set `HOST_IP` to the machine IP you want the shared stream URL to use.
