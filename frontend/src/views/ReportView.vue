<template>
  <div class="page">
    <div class="page-title">📋 复盘报告</div>
    <div style="display:flex;gap:8px;margin-bottom:var(--space-sm)">
      <select v-model="selectedPeriod" style="flex-shrink:0;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:6px 10px;font-size:var(--text-caption);background:var(--surface-1);color:var(--text-primary);">
        <option value="weekly">近 7 天</option>
        <option value="biweekly">近 14 天</option>
        <option value="monthly">近 30 天</option>
      </select>
      <button
        class="btn btn-primary"
        @click="generateReport"
        :disabled="generating"
        style="flex:1"
      >
        {{ generating ? '生成中…' : '生成新报告' }}
      </button>
    </div>
    <div v-if="genMsg" class="gen-msg">{{ genMsg }}</div>

    <div v-if="loading" class="empty-state">
      <div class="empty-state-text">加载中…</div>
    </div>
    <div v-else-if="!reports.length" class="empty-state">
      <div class="empty-state-icon">📋</div>
      <div class="empty-state-text">暂无复盘报告</div>
    </div>
    <div v-else>
      <div
        v-for="r in reports"
        :key="r.id"
        class="report-item"
        @click="view(r.id)"
      >
        <div class="report-header">
          <div class="report-period">{{ r.period }}</div>
          <button class="btn btn-ghost" style="padding:2px 6px;font-size:11px;flex-shrink:0" @click.stop="deleteReport(r.id)">🗑</button>
        </div>
        <div class="report-meta">
          <span>{{ r.dateRange }}</span>
        </div>
        <div class="report-excerpt">{{ r.excerpt }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface ReportItem {
  id: string
  period: string
  dateRange: string
  expertCount: number
  excerpt: string
}

const reports = ref<ReportItem[]>([])
const loading = ref(true)
const selectedPeriod = ref('weekly')
const generating = ref(false)
const genMsg = ref('')

function _formatTime(iso: string): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const mi = String(d.getMinutes()).padStart(2, '0')
    return `${mm}月${dd}日 ${hh}:${mi}`
  } catch {
    const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/)
    if (m) return `${Number(m[2])}月${Number(m[3])}日`
    return ''
  }
}

function _periodLabel(fn: string): string {
  if (/weekly/i.test(fn)) return '📅 自知周报'
  if (/monthly/i.test(fn)) return '📅 自知月报'
  return '📅 自知报告'
}

async function fetchReports() {
  loading.value = true
  try {
    const res = await fetch('/api/reports')
    if (res.ok) {
      const data = await res.json()
      reports.value = (data || []).map((r: any) => ({
        id: r.id,
        period: _periodLabel(r.filename || ''),
        dateRange: _formatTime(r.created_at),
        expertCount: r.expert_count || 0,
        excerpt: r.excerpt || '',
      }))
    }
  } catch { /* keep empty */ }
  loading.value = false
}

async function generateReport() {
  generating.value = true
  genMsg.value = ''
  try {
    const res = await fetch('/api/reports/generate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({period: selectedPeriod.value}) })
    const data = await res.json()
    if (data.ok && data.report_id) {
      await fetchReports()
    } else if (data.message) {
      genMsg.value = data.message
    }
  } catch {
    genMsg.value = '生成失败，请检查 LLM 配置'
  }
  generating.value = false
}

function view(id: string) {
  window.open(`/api/reports/${id}`, '_blank')
}

async function deleteReport(id: string) {
  if (!confirm('确定删除这份报告？')) return
  try {
    await fetch(`/api/reports/${id}`, { method: 'DELETE' })
    reports.value = reports.value.filter(r => r.id !== id)
  } catch { /* ignore */ }
}

onMounted(fetchReports)
</script>

<style scoped>
.gen-msg {
  background: var(--hairline);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: var(--text-caption);
  color: var(--ink-muted);
  margin-bottom: var(--space-md);
}
.report-header { display: flex; justify-content: space-between; align-items: center; }
</style>
