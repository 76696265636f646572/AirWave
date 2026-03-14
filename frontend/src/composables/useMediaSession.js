import { watch } from "vue";

import { useLibraryState } from "./useLibraryState";
import { usePlaybackState } from "./usePlaybackState";

const FALLBACK_ARTWORK_URL = "/web-app-manifest-192x192.png";
const ARTWORK_SIZES = [96, 128, 192, 256, 384, 512];

function buildArtwork(thumbnailUrl) {
  const src = thumbnailUrl || FALLBACK_ARTWORK_URL;
  return ARTWORK_SIZES.map((size) => ({
    src,
    sizes: `${size}x${size}`,
    type: "image/png",
  }));
}

export function useMediaSession() {
  if (typeof navigator === "undefined" || !("mediaSession" in navigator)) {
    return;
  }

  const { playbackState } = usePlaybackState();
  const { togglePause, skipCurrent, previousTrack } = useLibraryState();

  function updateMetadata() {
    const state = playbackState.value;

    navigator.mediaSession.metadata = new MediaMetadata({
      title: state?.now_playing_title || "Airwave",
      artist: state?.now_playing_channel || "",
      album: "",
      artwork: buildArtwork(state?.now_playing_thumbnail_url),
    });

    const isPlaying = state?.mode === "playing" && !state?.paused;
    navigator.mediaSession.playbackState = isPlaying ? "playing" : "paused";
  }

  navigator.mediaSession.setActionHandler("play", () => togglePause());
  navigator.mediaSession.setActionHandler("pause", () => togglePause());
  navigator.mediaSession.setActionHandler("previoustrack", () => previousTrack());
  navigator.mediaSession.setActionHandler("nexttrack", () => skipCurrent());

  watch(playbackState, updateMetadata, { immediate: true, deep: true });
}
