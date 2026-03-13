<template>
  <section class="min-h-0 h-full overflow-hidden rounded-xl border border-neutral-700 p-3 flex flex-col surface-panel">
    <div class="flex items-center justify-between gap-3">
      <h2 class="text-2xl font-bold">Queue</h2>
      <UButton
        type="button"
        color="error"
        variant="soft"
        size="xs"
        :disabled="!queue.length"
        class="shrink-0 cursor-pointer"
        @click="clearQueue"
      >
        Clear Queue
      </UButton>
    </div>
    <div class="mt-3 min-h-0 flex-1 pr-1">
      <UScrollArea :ui="{ viewport: 'gap-2 pr-1' }" class="h-full min-h-0">
          <ul class="space-y-2">
            <li v-for="item in playingItems" :key="item.id">
              <Song :item="item" mode="queue" :playlists="playlists" />
            </li>
          </ul>
          <VueDraggable
            v-model="queuedItems"
            tag="ul"
            class="space-y-2"
            :animation="150"
            :delay="200"
            :delay-on-touch-only="true"
            ghost-class="queue-drag-ghost"
            chosen-class="queue-drag-chosen"
            @end="onReorderEnd"
          >
            <li v-for="item in queuedItems" :key="item.id">
              <Song :item="item" mode="queue" :playlists="playlists" />
            </li>
          </VueDraggable>
      </UScrollArea>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";

import { VueDraggable } from "vue-draggable-plus";

import { useLibraryState } from "../composables/useLibraryState";

import Song from "./Song.vue";

const { queue, playlists, clearQueue, reorderQueueItem } = useLibraryState();

const playingItems = computed(() => queue.value.filter((item) => item.status === "playing"));

const queuedItems = ref([]);

function syncQueuedItems() {
  const queued = queue.value.filter((item) => item.status === "queued");
  queuedItems.value = [...queued];
}

watch(queue, syncQueuedItems, { immediate: true });

function onReorderEnd(evt) {
  const { oldIndex, newIndex } = evt;
  if (oldIndex === newIndex) return;
  const item = queuedItems.value[newIndex];
  if (!item?.id) return;
  reorderQueueItem(item.id, newIndex);
}
</script>
