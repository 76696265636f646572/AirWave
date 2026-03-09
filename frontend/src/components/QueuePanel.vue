<template>
  <section class="min-h-0 h-full overflow-hidden rounded-xl border border-neutral-700 bg-neutral-900 p-3 flex flex-col">
    <h2 class="text-2xl font-bold">Queue</h2>
    <ul class="mt-3 min-h-0 flex-1 space-y-2 overflow-auto pr-1">
      <li v-for="item in queue" :key="item.id" class="rounded-md border border-neutral-700 p-2">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <span class="block break-words text-sm font-medium">#{{ item.queue_position }} {{ item.title || item.source_url }}</span>
            <span class="text-xs text-neutral-400">{{ item.status }} · {{ item.channel || "unknown" }}</span>
          </div>
          <div class="flex flex-wrap justify-end gap-1">
            <UButton
              type="button"
              color="neutral"
              variant="outline"
              size="xs"
              @click="$emit('reorder', { itemId: item.id, newPosition: Math.max(0, item.queue_position - 2) })"
            >
              Up
            </UButton>
            <UButton
              type="button"
              color="neutral"
              variant="outline"
              size="xs"
              @click="$emit('reorder', { itemId: item.id, newPosition: item.queue_position })"
            >
              Down
            </UButton>
            <UButton type="button" color="error" variant="ghost" size="xs" @click="$emit('remove', item.id)">
              Remove
            </UButton>
            <UButton
              type="button"
              color="primary"
              variant="soft"
              size="xs"
              :disabled="!activePlaylistId"
              @click="$emit('save-to-playlist', item)"
            >
              Save
            </UButton>
          </div>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
defineProps({
  queue: {
    type: Array,
    default: () => [],
  },
  activePlaylistId: {
    type: Number,
    default: null,
  },
});

defineEmits(["remove", "reorder", "save-to-playlist"]);
</script>
