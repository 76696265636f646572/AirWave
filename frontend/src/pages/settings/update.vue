<template>
  <div>
    <h2 class="text-2xl font-bold">Update</h2>
    <p class="mt-1 text-sm text-muted">
      Manage included binaries (yt-dlp, ffmpeg, deno) and install updates.
    </p>

    <div v-if="loading" class="mt-6 text-sm text-muted">Loading...</div>
    <div v-else-if="errorMessage" class="mt-6 text-sm text-red-400">{{ errorMessage }}</div>

    <div v-else class="mt-6 space-y-4">
      <div
        v-for="(b, idx) in binaries"
        :key="b.name"
        class="rounded-lg border border-neutral-700 p-4 surface-panel"
      >
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="min-w-0">
            <div class="font-medium">{{ b.name }}</div>
            <div class="mt-1 text-sm text-muted truncate" :title="b.path">{{ b.path }}</div>
            <div class="mt-1 text-xs text-muted">
              Installed: {{ b.version || "—" }}
              <span v-if="updatesById[b.name]">
                · Latest: {{ updatesById[b.name]?.latest || "—" }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <UButton
              v-if="b.is_system"
              variant="soft"
              color="neutral"
              size="sm"
              disabled
              label="System (read-only)"
            />
            <UButton
              v-else-if="updatesById[b.name]?.has_update"
              :loading="installing === b.name"
              size="sm"
              label="Update"
              @click="installBinary(b.name)"
            />
            <UButton
              v-else-if="!b.version && updatesById[b.name]"
              :loading="installing === b.name"
              size="sm"
              label="Install"
              @click="installBinary(b.name)"
            />
            <span v-else-if="b.version && !updatesById[b.name]?.has_update" class="text-xs text-muted">
              Up to date
            </span>
          </div>
        </div>
      </div>

      <div v-if="binaries.length === 0 && !loading" class="text-sm text-muted">
        No binary information available.
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { fetchJson } from "../../composables/useApi";

const binaries = ref([]);
const updates = ref([]);
const loading = ref(true);
const errorMessage = ref("");
const installing = ref("");

const updatesById = computed(() => {
  const byId = {};
  for (const u of updates.value) {
    byId[u.name] = u;
  }
  return byId;
});

async function load() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const [binRes, updRes] = await Promise.all([
      fetchJson("/api/binaries"),
      fetchJson("/api/binaries/updates"),
    ]);
    binaries.value = binRes.binaries || [];
    updates.value = updRes.updates || [];
  } catch (e) {
    errorMessage.value = e?.message || "Failed to load binary status.";
  } finally {
    loading.value = false;
  }
}

async function installBinary(name) {
  installing.value = name;
  errorMessage.value = "";
  try {
    await fetchJson("/api/binaries/install", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    await load();
  } catch (e) {
    errorMessage.value = e?.message || `Failed to install ${name}.`;
  } finally {
    installing.value = "";
  }
}

onMounted(load);
</script>
