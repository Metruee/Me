<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div>
        <div class="sidebar-brand">Me · 自知</div>
        <div class="sidebar-sub">自知者明</div>
      </div>
      <nav class="sidebar-nav">
        <button
          v-for="t in tabs"
          :key="t.path"
          class="sidebar-item"
          :class="{ active: $route.path === t.path }"
          @click="$router.push(t.path)"
        >
          <span class="tab-icon">{{ t.icon }}</span>
          <span>{{ t.label }}</span>
        </button>
      </nav>
    </aside>

    <main class="app-main">
      <div class="app">
        <!-- Header -->
        <header class="header">
          <div class="header-inner">
            <div>
              <div class="header-title">Me · 自知</div>
              <div class="header-subtitle">自知者明</div>
            </div>
            <div class="header-actions">
              <button class="theme-btn" @click="toggleTheme" :title="theme === 'dark' ? '切换浅色' : '切换深色'">
                {{ theme === 'dark' ? '🌙' : '☀️' }}
              </button>
              <button class="btn-icon" title="设置" @click="$router.push('/settings')">⚙️</button>
            </div>
          </div>
        </header>

        <!-- Expert Bar (only on chat page) -->
        <div v-if="$route.path === '/chat'" class="expert-bar">
          <div class="expert-list">
            <div
              v-for="e in experts"
              :key="e.id"
              class="expert-chip"
              :class="{ active: e.id === currentExpert?.id }"
              @click="switchExpert(e)"
            >
              <span class="dot" :style="{ background: colors[e.id] || '#c6984a' }"></span>
              <span>{{ e.emoji }} {{ e.name }}</span>
            </div>
          </div>
        </div>

        <!-- Summon Overlay (global in App.vue) -->
        <div v-if="animating" class="summon-overlay" @click="animating = false">
          <div class="summon-card">
            <div class="summon-glow">{{ summonEmoji }}</div>
            <div class="summon-title">{{ summonTitle }}</div>
            <div class="summon-desc">{{ summonDesc }}</div>
            <button class="summon-cancel" @click="animating = false">✕ 取消</button>
          </div>
        </div>

        <!-- Toast -->
        <div v-if="toast" class="toast-msg">{{ toast }}</div>

        <!-- Pages via Router -->
        <div class="page-view"><router-view /></div>

        <!-- Bottom Nav -->
        <nav class="tab-nav">
          <button
            v-for="t in tabs"
            :key="t.path"
            class="tab-item"
            :class="{ active: $route.path === t.path }"
            @click="$router.push(t.path)"
          >
            <span class="tab-icon">{{ t.icon }}</span>
            <span>{{ t.label }}</span>
          </button>
        </nav>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, provide, onMounted } from 'vue'
import type { Expert, Message } from './types'

/* ── Tabs ── */
const tabs = [
  { path: '/chat', label: '对话', icon: '💬' },
  { path: '/archive', label: '档案馆', icon: '📚' },
  { path: '/report', label: '复盘', icon: '📋' },
  { path: '/skills', label: '技能', icon: '🔧' },
  { path: '/daoben', label: '道痕', icon: '🪨' },
  { path: '/experts', label: '专家', icon: '🎭' },
]

/* ── Expert Colors ── */
const colors: Record<string, string> = {
  taishiling: '#c6984a',
  zhongkui: '#8b5e3c',
  chiyou: '#b8453a',
  bigan: '#6b9e6b',
  tanlang: '#7b5ea7',
  zaojun: '#c45d3c',
  qibo: '#4a7d6e',
  cangjie: '#b8a870',
}

/* ── 8 Experts ── */
const ALL_EXPERTS: Expert[] = [
  { id: 'taishiling', key: 'taishiling', name: '太史令', title: '万象录史官', emoji: '📜', color: '#c6984a', domain: 'all', summon: '太史令', response: '史官在侧，秉笔直书。请说。' },
  { id: 'zhongkui', key: 'zhongkui', name: '钟馗', title: '镇心判官', emoji: '⚔️', color: '#8b5e3c', domain: '自我核心', summon: '钟馗', response: '心中有鬼，方须照剑。你是来伏魔的，还是来求饶的？' },
  { id: 'chiyou', key: 'chiyou', name: '蚩尤', title: '兵主战神', emoji: '🐉', color: '#b8453a', domain: '事业', summon: '蚩尤', response: '畏刀避剑之人，不配站在我的旗下。说敌情。' },
  { id: 'bigan', key: 'bigan', name: '比干', title: '无心财判', emoji: '⚖️', color: '#6b9e6b', domain: '财富', summon: '比干', response: '我无心，故不偏。把你那笔糊涂账，摊开来。' },
  { id: 'tanlang', key: 'tanlang', name: '贪狼', title: '欲海明灯', emoji: '🐺', color: '#7b5ea7', domain: '人性', summon: '贪狼', response: '你每一寸欲望都瞒不过我。这次想喂养哪一个？' },
  { id: 'zaojun', key: 'zaojun', name: '司命灶君', title: '家宅镜鉴', emoji: '🔥', color: '#c45d3c', domain: '亲密关系', summon: '灶君', response: '灶火明堂，司命在场。家宅之事，从实道来。' },
  { id: 'qibo', key: 'qibo', name: '岐伯', title: '身土鉴察官', emoji: '🌿', color: '#4a7d6e', domain: '健康', summon: '岐伯', response: '上古天真，问于天师。你哪里失了调和？' },
  { id: 'cangjie', key: 'cangjie', name: '仓颉', title: '道痕观察者', emoji: '🏺', color: '#b8a870', domain: '自知', summon: '仓颉', response: '每一笔都是一次看见。你看到了什么？是河底的石头，还是水面上的波纹？' },
]

/* ── Reactive State ── */
const sessionId = ref('default')
const messages = ref<Message[]>([])
const sessions = ref<{id:string; label:string; date:string}[]>([])
const currentExpert = ref<Expert>(ALL_EXPERTS[0])
const experts = ref<Expert[]>(ALL_EXPERTS)
const animating = ref(false)
const summonEmoji = ref('')
const summonTitle = ref('')

async function loadSessions() {
  try {
    const res = await fetch('/api/sessions')
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data) && data.length > 0) {
        sessions.value = data
      } else {
        await createSession(true)
        return
      }
    }
  } catch {}
  if (!sessions.value.length) {
    sessions.value = [{id:'default', label:'默认对话', date: new Date().toLocaleDateString('zh-CN')}]
  }
  const savedId = localStorage.getItem('me-current-session')
  if (savedId && sessions.value.find((s: any) => s.id === savedId)) {
    sessionId.value = savedId
  } else {
    sessionId.value = sessions.value[0]?.id || 'default'
  }
}

function renameSession(id: string, label: string) {
  const s = sessions.value.find(x => x.id === id)
  if (s) s.label = label
  // 后端更新
  fetch(`/api/sessions/${id}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({label}) }).catch(()=>{})
}

// 恢复历史对话
async function restoreHistory() {
  try {
    const res = await fetch(`/api/sessions/${sessionId.value}/history`)
    if (!res.ok) return
    const data = await res.json()
    if (!Array.isArray(data) || data.length === 0) return
    messages.value = []
    for (const m of data) {
      if (m.role === 'user') {
        messages.value.push({ type: 'user', content: m.content, timestamp: Date.now() })
      } else if (m.role === 'assistant' || m.role === 'expert') {
        messages.value.push({
          type: 'expert',
          content: m.content,
          expertId: m.expert_id || 'taishiling',
          expertName: experts.value.find((e: Expert) => e.id === (m.expert_id || 'taishiling'))?.name || '',
          timestamp: Date.now(),
        })
      }
    }
    const lastExpert = data.filter((m: any) => m.role === 'assistant' || m.role === 'expert').pop()
    if (lastExpert?.expert_id) {
      const e = experts.value.find((x: Expert) => x.id === lastExpert.expert_id)
      if (e) currentExpert.value = e
    }
  } catch { /* ignore */ }
}

async function createSession(initial = false): Promise<string> {
  const d = new Date()
  const label = initial ? '默认对话' : `对话 ${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
  let id = 'default'
  if (!initial) {
    try {
      const res = await fetch('/api/sessions', { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        id = data.id  // 使用后端返回的 ID，保持一致
      }
    } catch {}
  }
  sessions.value.unshift({id, label, date: d.toLocaleDateString('zh-CN')})
  localStorage.setItem('me-current-session', id)
  return id
}

function switchSession(id: string) {
  sessionId.value = id
  messages.value = []
  currentExpert.value = ALL_EXPERTS[0]
  localStorage.setItem('me-current-session', id)
  restoreHistory()
}

async function deleteSession(id: string) {
  try { await fetch(`/api/session/${id}`, { method: 'DELETE' }) } catch {}
  sessions.value = sessions.value.filter(s => s.id !== id)
  if (sessionId.value === id) {
    if (sessions.value.length) switchSession(sessions.value[0].id)
    else createSession(true)
  }
}
const summonDesc = ref('')
const toast = ref('')
let summonTimer: number | null = null

/* ── Theme ── */
const theme = ref<'dark' | 'light'>((localStorage.getItem('me-theme') as 'dark' | 'light') || 'dark')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('me-theme', theme.value)
}
onMounted(async () => {
  document.documentElement.setAttribute('data-theme', theme.value)
  await loadSessions()
  restoreHistory()
})

/* ── Expert Switch ── */
function switchExpert(expert: Expert) {
  currentExpert.value = expert
}

/* ── Summon ── */
function triggerSummon(expertId: string) {
  const expert = experts.value.find(e => e.id === expertId)
  if (!expert) return
  switchExpert(expert)
  summonEmoji.value = expert.emoji
  summonTitle.value = `召唤 ${expert.name}`
  summonDesc.value = expert.title
  animating.value = true
  if (summonTimer) clearTimeout(summonTimer)
  summonTimer = window.setTimeout(() => {
    animating.value = false
  }, 1800)
}

function showToast(msg: string, duration = 2000) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, duration)
}

/* ── Chat Logic ── */
async function handleSend(text: string, isFileUpload = false) {
  messages.value.push({ type: 'user', content: text, timestamp: Date.now() })

  // Summon detection
  const summonMatch = experts.value.find(e =>
    text.includes(e.summon) && text.length < 15 && e.id !== currentExpert.value.id
  )
  if (summonMatch) {
    triggerSummon(summonMatch.id)
    return
  }

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, expert_id: currentExpert.value.id, session_id: sessionId.value, is_file_upload: isFileUpload }),
    })
    const data = await res.json()

    if (data.switch_type === 'summon') {
      const expert = experts.value.find((e: Expert) => e.id === data.expert_id)
      if (expert) {
        triggerSummon(expert.id)
        if (data.system_message)
          messages.value.push({ type: 'system', content: data.system_message, timestamp: Date.now() })
        switchExpert(expert)
      }
    } else if (data.switch_type === 'auto') {
      if (data.system_message)
        messages.value.push({ type: 'system', content: data.system_message, timestamp: Date.now() })
      const expert = experts.value.find((e: Expert) => e.id === data.expert_id)
      if (expert) currentExpert.value = expert
    }

    if (data.llm_error) {
      messages.value.push({ type: 'system', content: data.llm_error, timestamp: Date.now() })
    } else {
      messages.value.push({
        type: 'expert',
        content: data.reply,
        expertId: data.expert_id,
        expertName: experts.value.find((e: Expert) => e.id === data.expert_id)?.name || '',
        archived: data.archived || false,
        timestamp: Date.now(),
      })
    }
  } catch {
    messages.value.push({
      type: 'system',
      content: '抱歉，模型响应超时或不可用，已尝试重试，请稍后再试。',
      timestamp: Date.now(),
    })
  }
}

/* ── Provide to children ── */
provide('messages', messages)
provide('currentExpert', currentExpert)
provide('experts', experts)
provide('colors', colors)
provide('onSend', handleSend)
provide('onSwitch', switchExpert)
provide('triggerSummon', triggerSummon)
provide('showToast', showToast)
provide('sessionId', sessionId)
provide('sessions', sessions)
provide('createSession', createSession)
provide('switchSession', switchSession)
provide('deleteSession', deleteSession)
provide('renameSession', renameSession)
</script>
