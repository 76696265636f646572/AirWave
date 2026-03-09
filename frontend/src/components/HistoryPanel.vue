<template>
  <section class="min-h-0 overflow-hidden rounded-xl border border-neutral-700 bg-neutral-900 p-3">
    <div class="flex items-center justify-between gap-3">
      <h2 class="text-2xl font-bold">Play History</h2>
      <button
        type="button"
        :disabled="!history.length"
        class="shrink-0 rounded-md border border-red-700 bg-red-950 px-2 py-1 text-xs font-medium text-red-200 hover:bg-red-900 disabled:cursor-not-allowed disabled:opacity-40"
        @click="$emit('clear')"
      >
        Clear History
      </button>
    </div>
    <ul class="mt-3 max-h-[30vh] space-y-1 overflow-auto pr-1">
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
