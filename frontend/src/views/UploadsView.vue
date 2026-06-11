<template>
  <div class="page">
    <div class="page-title">📂 导入文件</div>
    <div style="display:flex;align-items:center;gap:8px;margin:12px 0 16px;">
      <button class="btn btn-secondary" style="font-size:12px;padding:4px 10px;" @click="$router.push('/archive')">← 返回档案馆</button>
    </div>
    <div v-if="loading" class="empty-state">
      <div class="empty-state-text">加载中…</div>
    </div>
    <div v-else-if="!files.length" class="empty-state">
      <div class="empty-state-icon">📭</div>
      <div class="empty-state-text">暂无导入文件</div>
    </div>
    <div v-else class="file-list">
      <div v-for="f in files" :key="f.name" class="file-item">
        <div class="file-info">
          <span class="file-icon">{{ iconFor(f.ext) }}</span>
          <div class="file-meta">
            <div class="file-name">{{ f.name }}</div>
            <div class="file-detail">{{ formatSize(f.size) }} · {{ formatDate(f.mtime) }}</div>
          </div>
        </div>
        <button class="btn btn-ghost" style="color:var(--danger);font-size:12px;padding:2px 8px;" @click="deleteFile(f.name)">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface UploadFile {
  name: string
  size: number
  mtime: string
  ext: string
}

const files = ref<UploadFile[]>([])
const loading = ref(true)

onMounted(async () => {
  loading.value = true
  try {
    const res = await fetch('/api/uploads')
    if (res.ok) {
      const data = await res.json()
      files.value = data.files || []
    }
  } catch {}
  loading.value = false
})

function iconFor(ext: string): string {
  const map: Record<string, string> = {
    '.xlsx': '📊', '.xls': '📊', '.csv': '📊',
    '.pdf': '📕', '.txt': '📝', '.md': '📝',
    '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.webp': '🖼️',
    '.docx': '📄', '.doc': '📄',
  }
  return map[ext] || '📎'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN')
}

async function deleteFile(name: string) {
  if (!window.confirm(`确定删除 ${name}？`)) return
  try {
    const res = await fetch(`/api/uploads/${encodeURIComponent(name)}`, { method: 'DELETE' })
    if (res.ok) {
      files.value = files.value.filter(f => f.name !== name)
    }
  } catch {}
}
</script>

<style scoped>
.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}
.file-icon { font-size: 22px; flex-shrink: 0; }
.file-meta { overflow: hidden; }
.file-name {
  font-size: 13px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-detail {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}
</style>
