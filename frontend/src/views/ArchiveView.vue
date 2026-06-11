<template>
  <div class="page">
    <div class="page-title">📚 档案馆</div>
    <div class="archive-filter">
      <div
        v-for="t in themes"
        :key="t.key"
        class="filter-chip"
        :class="{ active: activeTheme === t.key }"
        @click="activeTheme = t.key"
      >{{ t.label }}</div>
      <div class="filter-chip" style="margin-left:auto;" @click="$router.push('/archive/uploads')">📂 导入文件</div>
    </div>
    <div v-if="loading" class="empty-state">
      <div class="empty-state-text">加载中…</div>
    </div>
    <div v-else-if="!filteredItems.length" class="empty-state">
      <div class="empty-state-icon">📭</div>
      <div class="empty-state-text">暂无归档条目</div>
    </div>
    <div v-else>
      <div
        v-for="item in filteredItems"
        :key="item.id"
        class="archive-item"
        @click="$router.push('/archive/' + item.id)"
      >
        <div class="archive-item-header">
          <span class="archive-item-tag">{{ item.tag }}</span>
          <span class="archive-item-date">{{ item.date }}</span>
        </div>
        <div class="archive-item-summary">{{ item.summary }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const themes = [
  { key: 'all', label: '全部' },
  { key: '自我核心', label: '自我核心' },
  { key: '财富', label: '财富' },
  { key: '事业', label: '事业' },
  { key: '人性', label: '人性' },
  { key: '亲密关系', label: '亲密关系' },
  { key: '健康', label: '健康' },
  { key: '自知', label: '自知' },
]

const activeTheme = ref('all')
const loading = ref(true)

interface ArchiveItem {
  id: string
  tag: string
  date: string
  summary: string
}

const items = ref<ArchiveItem[]>([])

const filteredItems = computed(() => {
  if (activeTheme.value === 'all') return items.value
  return items.value.filter(i => i.tag === activeTheme.value)
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await fetch('/api/knowledge/entries?limit=50')
    if (res.ok) {
      const data = await res.json()
      items.value = (data || []).map((e: any) => ({
        id: e.id || String(Math.random()),
        tag: e.theme_main || '未归类',
        date: e.created_at ? new Date(e.created_at).toLocaleDateString('zh-CN') : '',
        summary: e.summary || e.original_text?.slice(0, 120) || '',
      }))
    }
  } catch { /* keep empty */ }
  loading.value = false
})
</script>
