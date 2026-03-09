<template>
  <section class="min-h-0 h-full overflow-hidden rounded-xl border border-neutral-700 bg-neutral-900 p-3 flex flex-col">
    <div class="flex items-center justify-between gap-3">
      <h2 class="text-2xl font-bold">Play History</h2>
      <UButton
        type="button"
        color="error"
        variant="soft"
        size="xs"
        :disabled="!history.length"
        class="shrink-0"
        @click="$emit('clear')"
      >
        Clear History
      </UButton>
    </div>
    <ul class="mt-3 min-h-0 flex-1 space-y-1 overflow-auto pr-1">
      <li
        v-for="item in history"
        :key="item.id"
        class="flex items-center justify-between gap-2 rounded-md border border-neutral-700 px-2 py-2"
      >
        <span class="min-w-0 flex-1 truncate text-sm">{{ item.title || item.source_url }}</span>
        <span class="text-xs text-neutral-400">{{ item.status }}</span>
      </li>
    </ul>
  </section>
</template>

<script setup>
defineProps({
  history: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["clear"]);
</script>
