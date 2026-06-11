<template>
  <div class="page">
    <!-- Header -->
    <header class="page-header">🪨 道痕日记</header>
    <div style="text-align:center;font-size:11px;color:var(--ink-muted);margin-bottom:var(--space-md);">
      来自《人选天选论》，感谢路飞大神的作品提供的思路引导
    </div>

    <!-- Stats Bar -->
    <div style="display:flex;align-items:center;justify-content:center;gap:var(--space-md);margin-bottom:var(--space-md)">
      <router-link to="/daoben/dashboard" class="btn btn-primary" style="text-decoration:none;padding:8px 16px;font-size:13px;">📊 回看仪表盘</router-link>
    </div>
    <div v-if="topStones.length" class="stats-bar">
      <span class="stats-label">重复出现的石头：</span>
      <span v-for="(s, i) in topStones" :key="i" class="stone-chip">
        {{ s.stone }} ×{{ s.count }}
      </span>
    </div>

    <!-- New Entry Form (独立于列表) -->
    <div v-if="showForm" class="card card-accent" style="margin-bottom:var(--space-lg)">
      <h3 style="font-size:var(--text-title);margin-bottom:var(--space-md);color:var(--accent)">新道痕</h3>

      <div class="daoben-field">
        <label>1. 今天最起波澜的一件事</label>
        <textarea v-model="form.event_text" rows="2" placeholder="发生了什么…"></textarea>
      </div>
      <div class="daoben-field">
        <label>2. 当时我的第一反应</label>
        <textarea v-model="form.first_reaction" rows="2" placeholder="最直接的感觉…"></textarea>
      </div>
      <div class="daoben-field">
        <label>3. 我其实想得到什么（贪梦）</label>
        <textarea v-model="form.greed" rows="2" placeholder="具体的，不要写大词…"></textarea>
      </div>
      <div class="daoben-field">
        <label>4. 我其实在害怕什么（恐惧）</label>
        <textarea v-model="form.fear" rows="2" placeholder="最小、最直接的那个怕…"></textarea>
      </div>
      <div class="daoben-field">
        <label>5. 我给自己找了什么理由（自洽）</label>
        <textarea v-model="form.excuses" rows="2" placeholder="让自己舒服的解释…"></textarea>
      </div>
      <div class="daoben-field">
        <label>6. 今天捞出来的主石头</label>
        <input v-model="form.main_stone" placeholder="一句定论，如：怕被看轻" />
      </div>
      <div class="daoben-field">
        <label>7. 如果明天再遇到，我准备怎么选</label>
        <textarea v-model="form.tomorrow_plan" rows="2" placeholder="一句话，行动方案…"></textarea>
      </div>

      <div style="display:flex;gap:var(--space-sm);margin-top:var(--space-md)">
        <button class="btn btn-primary" @click="submitEntry" :disabled="!form.event_text.trim()">
          入库
        </button>
        <button class="btn btn-ghost" @click="showForm = false; resetForm()">
          取消
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="page-body" v-if="entries.length">
      <!-- Filters -->
      <div class="filter-row">
        <button
          class="filter-tag" :class="{ active: searchQuery === '' && !showForm }"
          @click="searchQuery = ''; showForm = false"
        >全部</button>
        <button
          class="filter-tag" :class="{ active: showForm }"
          @click="showForm = !showForm; searchQuery = ''"
        >+ 记道痕</button>
      </div>

      <!-- Search -->
      <div style="margin-bottom:var(--space-lg)">
        <input
          v-model="searchQuery"
          placeholder="搜索道痕…"
          style="width:100%;height:40px;padding:0 14px;border:1px solid var(--hairline-strong);border-radius:var(--radius-pill);font-size:var(--text-body);background:var(--canvas);outline:none"
          @input="fetchEntries()"
        />
      </div>

      <!-- Entry List -->
      <div v-for="e in entries" :key="e.id" class="card" style="cursor:pointer" @click="toggleDetail(e.id)">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <div style="flex:1">
            <div class="card-date">{{ formatDate(e.created_at) }}
              <span v-if="e.expert_id" style="margin-left:8px;opacity:0.6">via {{ e.expert_id }}</span>
              <span v-if="e.source === 'chat'" style="margin-left:4px;opacity:0.5;font-size:11px">💬</span>
            </div>
            <div class="card-title">{{ e.main_stone || '未命名石头' }}</div>
            <div class="card-body" style="font-size:var(--text-caption)">{{ e.event_text.slice(0, 120) }}{{ e.event_text.length > 120 ? '…' : '' }}</div>
          </div>
          <button
            class="btn btn-ghost"
            style="flex-shrink:0;padding:4px 8px;font-size:11px"
            @click.stop="deleteEntry(e.id)"
          >🗑</button>
        </div>

        <!-- Expanded Detail -->
        <div v-if="expandedId === e.id" style="margin-top:var(--space-md);padding-top:var(--space-md);border-top:1px solid var(--hairline)">
          <div class="detail-row"><span class="detail-label">💬 事实</span>{{ e.event_text }}</div>
          <div class="detail-row"><span class="detail-label">😶 第一反应</span>{{ e.first_reaction || '—' }}</div>
          <div class="detail-row"><span class="detail-label">🪙 贪梦 (想要)</span>{{ e.greed || '—' }}</div>
          <div class="detail-row"><span class="detail-label">🪙 恐惧 (怕)</span>{{ e.fear || '—' }}</div>
          <div class="detail-row"><span class="detail-label">🌊 自洽 (理由)</span>{{ e.excuses || '—' }}</div>
          <div class="detail-row"><span class="detail-label">🪨 主石头</span><strong>{{ e.main_stone }}</strong></div>
          <div class="detail-row"><span class="detail-label">🗺️ 明天的选择</span>{{ e.tomorrow_plan || '—' }}</div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!entries.length && !showForm" class="page-body" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
      <div style="font-size:48px;margin-bottom:var(--space-lg)">🪨</div>
      <h2 style="font-size:var(--text-headline);margin-bottom:var(--space-sm);color:var(--ink)">还没有道痕</h2>
      <p style="color:var(--ink-muted);max-width:280px;margin-bottom:var(--space-xl)">
        道痕是你观察自己河底石头的记录。<br/>每天捞一块石头，慢慢你就会看见自己思想的河流。
      </p>
      <button class="btn btn-primary" @click="showForm = true">
        记下第一条道痕
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { DaobenEntry } from '../types'

const entries = ref<DaobenEntry[]>([])
const topStones = ref<{ stone: string; count: number }[]>([])
const searchQuery = ref('')
const showForm = ref(false)
const expandedId = ref('')

const form = ref({
  event_text: '',
  first_reaction: '',
  greed: '',
  fear: '',
  excuses: '',
  main_stone: '',
  tomorrow_plan: '',
})

async function fetchEntries() {
  const params = new URLSearchParams({ limit: '100' })
  if (searchQuery.value) params.set('search', searchQuery.value)
  const res = await fetch(`/api/daoben/entries?${params}`)
  entries.value = await res.json()
}

async function fetchStats() {
  const res = await fetch('/api/daoben/stats')
  topStones.value = await res.json()
}

async function submitEntry() {
  if (!form.value.event_text.trim()) return
  await fetch('/api/daoben/entries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...form.value, source: 'manual' }),
  })
  resetForm()
  showForm.value = false
  await fetchEntries()
  await fetchStats()
}

function resetForm() {
  form.value = {
    event_text: '', first_reaction: '', greed: '',
    fear: '', excuses: '', main_stone: '', tomorrow_plan: '',
  }
}

function toggleDetail(id: string) {
  expandedId.value = expandedId.value === id ? '' : id
}

async function deleteEntry(id: string) {
  if (!confirm('确定删除这条道痕？')) return
  await fetch(`/api/daoben/entries/${id}`, { method: 'DELETE' })
  await fetchEntries()
  await fetchStats()
}

function formatDate(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => {
  fetchEntries()
  fetchStats()
})
</script>

<style scoped>
.stats-bar {
  padding: var(--space-sm) var(--space-lg);
  background: var(--accent-soft);
  border-bottom: 1px solid var(--hairline);
  font-size: var(--text-caption);
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.stats-label { opacity: 0.7; }
.stone-chip {
  background: var(--accent);
  color: #fff;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: var(--text-fine);
}

.daoben-field {
  margin-bottom: var(--space-sm);
}
.daoben-field label {
  display: block;
  font-size: var(--text-caption);
  color: var(--ink-secondary);
  margin-bottom: 4px;
  font-weight: var(--weight-medium);
}
.daoben-field textarea,
.daoben-field input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--hairline-strong);
  border-radius: var(--radius-sm);
  font-size: var(--text-body);
  font-family: var(--font-text);
  color: var(--ink);
  background: var(--canvas);
  outline: none;
  resize: vertical;
}
.daoben-field textarea:focus,
.daoben-field input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-soft);
}

.detail-row {
  padding: 6px 0;
  font-size: var(--text-body);
  line-height: 1.6;
  color: var(--ink);
}
.detail-label {
  display: inline-block;
  width: 130px;
  flex-shrink: 0;
  font-size: var(--text-caption);
  color: var(--ink-secondary);
  font-weight: var(--weight-medium);
}
</style>
