<template>
  <div class="flex flex-col w-full">
    <USlider
      :model-value="seekSliderValue"
      :min="0"
      :max="100"
      color="neutral"
      :size="size"
      :disabled="!canSeek"
      :ui="{ root: 'group', range: 'transition-colors group-hover:bg-primary', thumb: 'cursor-pointer opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100' }"
      class="w-full cursor-pointer"
      aria-label="Seek current track"
      @update:model-value="onSeekInput"
    />
    <div class="mt-2 flex w-full items-center justify-between text-xs text-muted">
      <span>{{ formatDuration(elapsedSeconds) }}</span>
      <span>{{ formatDuration(durationSeconds) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from "vue";
import { debounce } from "../composables/useDebounce";
import { formatDuration } from "../composables/useDuration";

const props = defineProps({
  progressPercent: { type: Number, default: 0 },
  elapsedSeconds: { type: Number, default: null },
  durationSeconds: { type: Number, default: null },
  canSeek: { type: Boolean, default: false },
  size: { type: String, default: "md" },
});

const emit = defineEmits(["seek"]);

const SEEK_DEBOUNCE_MS = 150;
const SEEK_IDLE_MS = 400;
const isSeeking = ref(false);
const localSeekPercent = ref(0);
let seekIdleTimer = null;

const seekSliderValue = computed(() =>
  isSeeking.value ? localSeekPercent.value : (props.progressPercent ?? 0)
);

function onSeekInput(value) {
  const percent = Array.isArray(value) ? value[0] : value;
  const num = Number(percent ?? 0);
  if (!Number.isFinite(num)) return;
  const clamped = Math.max(0, Math.min(100, num));
  isSeeking.value = true;
  localSeekPercent.value = clamped;
  if (seekIdleTimer) clearTimeout(seekIdleTimer);
  seekIdleTimer = setTimeout(() => {
    isSeeking.value = false;
    seekIdleTimer = null;
  }, SEEK_IDLE_MS);
  debouncedSeek(clamped);
}

const debouncedSeek = debounce((percent) => emit("seek", percent), SEEK_DEBOUNCE_MS);

onBeforeUnmount(() => {
  if (seekIdleTimer) clearTimeout(seekIdleTimer);
});
</script>
