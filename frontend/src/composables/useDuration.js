export function formatTotalDuration(totalSeconds) {
  const s = Math.max(0, Math.floor(Number(totalSeconds) || 0));
  const hrs = Math.floor(s / 3600);
  const mins = Math.floor((s % 3600) / 60);
  if (hrs > 0) return `${hrs} hr ${mins} min`;
  if (mins > 0) return `${mins} min`;
  return "< 1 min";
}

export function formatDuration(value) {
  const totalSeconds = Math.max(0, Math.floor(Number(value) || 0));
  const hours = Math.floor(totalSeconds / 3600);
  const mins = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const secs = String(totalSeconds % 60).padStart(2, "0");

  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${mins}:${secs}`;
  }

  return `${mins}:${secs}`;
}
