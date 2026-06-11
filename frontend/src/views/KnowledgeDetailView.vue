<template>
  <div style="display:flex;flex-direction:column;height:100%">
    <div class="page-header">
      <button class="btn btn-ghost" style="font-size:14px;padding:0;" @click="$router.back()">← 返回</button>
    </div>
    <div class="page-body">
      <div v-if="loading" class="text-center text-muted mt-lg">加载中…</div>
      <template v-else-if="entry">
        <div class="card" style="margin-bottom:var(--space-lg);">
          <div class="card-date">{{ fmt(entry.created_at) }}</div>
          <div class="card-title" style="font-size:var(--text-headline);">{{ entry.theme_main }}{{ entry.theme_sub ? ' · ' + entry.theme_sub : '' }}</div>
          <div v-if="entry.summary" class="card-body" style="margin-top:var(--space-md);padding:var(--space-md);background:var(--surface-2);border-radius:var(--radius-sm);white-space:pre-wrap;">{{ entry.summary }}</div>
          <div class="card-body" style="margin-top:var(--space-md);white-space:pre-wrap;line-height:1.8;">{{ entry.original_text }}</div>
        </div>
      </template>
      <div v-else class="text-center text-muted mt-lg">条目不存在</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const entryId = ref(route.params.entryId as string)
const entry = ref<any>(null)
const loading = ref(true)

async function load() {
  try {
    const res = await fetch(`/api/knowledge/entries/${entryId.value}`)
    if (res.ok) entry.value = await res.json()
  } catch { /* 404 */ }
  loading.value = false
}

function fmt(iso: string) {
  try { return new Date(iso).toLocaleDateString('zh-CN', { year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) }
  catch { return iso }
}

onMounted(load)
</script>
