<template>
  <div class="page-chat">
    <!-- === 会话选择栏 === -->
    <div class="session-bar">
      <div class="session-selector" @click="showSessionList = !showSessionList">
        <span class="session-name">{{ existingSessions.length ? '▾' : '' }} {{ currentSessionName }}</span>
      </div>
      <button class="btn btn-ghost" style="height:28px;font-size:11px;padding:0 10px;" @click="createSession">＋ 新对话</button>
    </div>

    <!-- 会话下拉列表 -->
    <div v-if="showSessionList && existingSessions.length" class="session-dropdown">
      <div
        v-for="s in existingSessions"
        :key="s.id"
        class="session-item"
        :class="{ active: s.id === sessionId }"
        @click="switchSession(s.id); showSessionList = false"
      >
        <div v-if="editingSessionId === s.id" style="flex:1;display:flex;gap:4px;" @click.stop>
          <input v-model="editingLabel" class="rename-input" @keydown.enter.prevent="commitRename()" @keydown.escape.prevent="editingSessionId = ''" />
          <button class="btn btn-primary" style="height:24px;font-size:10px;padding:0 8px;" @click.stop="commitRename()">✓</button>
        </div>
        <span v-else class="session-label" @click.stop="startRename(s)">{{ s.label }}</span>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="session-date">{{ s.date }}</span>
          <button class="btn btn-ghost" style="height:22px;font-size:10px;padding:0 6px;color:var(--danger);" @click.stop="deleteSession(s.id)">✕</button>
        </div>
      </div>
    </div>

    <div class="chat-area" ref="scrollEl" @click="showSessionList = false">
      <!-- Welcome -->
      <div v-if="!hasMessages" class="welcome">
        <div class="welcome-icon">🕯️</div>
        <div class="welcome-title">今夜，自知</div>
        <div class="welcome-desc">八位专家，一方烛火。<br>不迎合，不审判，只是照见。</div>
        <div class="quick-actions">
          <button class="quick-action" @click="quickSummon('zhongkui')">🪞 钟馗 · 直面自我</button>
          <button class="quick-action" @click="quickSummon('chiyou')">🐉 蚩尤 · 事业征伐</button>
          <button class="quick-action" @click="quickSummon('cangjie')">🏺 仓颉 · 道痕</button>
          <button class="quick-action" @click="quickSummon('taishiling')">📜 太史令 · 随心而谈</button>
        </div>
      </div>

      <!-- Messages -->
      <template v-for="(m, i) in messages" :key="i">
        <div v-if="m.type === 'system'" class="system-msg">{{ m.content }}</div>
        <div v-else class="message" :class="m.type">
          <div class="msg-avatar" :style="m.type === 'expert' ? { borderColor: getExpertColor(m.expertId), color: getExpertColor(m.expertId) } : {}">
            {{ m.type === 'user' ? '🙋' : getExpertEmoji(m.expertId) }}
          </div>
          <div>
            <div v-if="m.type === 'expert' && m.expertName" class="msg-meta">
              {{ getExpertEmoji(m.expertId) }} {{ m.expertName }} · {{ getExpertTitle(m.expertId) }}
            </div>
            <div class="msg-bubble" v-html="renderMarkdown(m.content)"></div>
          </div>
        </div>
      </template>
    </div>

    <div class="input-area">
      <div v-if="uploadingFile" class="upload-toast">上传中… {{ uploadFileName }}</div>
      <div class="input-row">
        <label class="upload-btn" title="上传文件">
          📎
          <input type="file" @change="handleUpload" style="display:none" />
        </label>
        <div class="input-wrapper">
          <textarea
            v-model="text"
            class="chat-input"
            placeholder="说点什么..."
            rows="1"
            @keydown.enter.exact.prevent="send"
            @input="autoResize"
            ref="textArea"
          ></textarea>
        </div>
        <button class="send-btn" @click="send">↑</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, watch, nextTick, computed } from 'vue'
import { marked } from 'marked'
import type { Expert, Message } from '../types'

const messages = inject('messages', ref<Message[]>([]))
const currentExpert = inject<Expert>('currentExpert')!
const experts = inject<Expert[]>('experts', [])
const colors = inject<Record<string, string>>('colors', {})
const onSend = inject<(text: string, isFileUpload?: boolean) => void>('onSend')!
const onSwitch = inject<(expert: Expert) => void>('onSwitch')!
const triggerSummon = inject<(expertId: string) => void>('triggerSummon', () => {})
const sessionId = inject<string>('sessionId', 'default')
const existingSessions = inject<any[]>('sessions', [])
const onCreateSession = inject<() => string>('createSession', () => 'default')
const onSwitchSession = inject<(id: string) => void>('switchSession', () => {})
const onDeleteSession = inject<(id: string) => void>('deleteSession', () => {})
const onRenameSession = inject<(id: string, label: string) => void>('renameSession', () => {})

const text = ref('')
const scrollEl = ref<HTMLElement>()
const textArea = ref<HTMLTextAreaElement>()
const showSessionList = ref(false)
const editingSessionId = ref('')
const editingLabel = ref('')
const uploadingFile = ref(false)
const uploadFileName = ref('')

const currentSessionName = computed(() => {
  const s = existingSessions.value.find((x: any) => x.id === sessionId.value)
  return s ? s.label : '默认对话'
})

async function createSession() {
  const id = await onCreateSession()
  onSwitchSession(id)
  showSessionList.value = false
}

function switchSession(id: string) {
  onSwitchSession(id)
  showSessionList.value = false
  editingSessionId.value = ''
}

function startRename(s: any) {
  editingSessionId.value = s.id
  editingLabel.value = s.label
}

function commitRename() {
  if (editingLabel.value.trim()) {
    onRenameSession(editingSessionId.value, editingLabel.value.trim())
  }
  editingSessionId.value = ''
}

function deleteSession(id: string) {
  if (!window.confirm('确定删除此对话？所有消息将被清除。')) return
  onDeleteSession(id)
  showSessionList.value = false
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  return marked.parse(text, { breaks: true }) as string
}

const hasMessages = computed(() => messages.value.filter(m => m.type !== 'system').length > 0)

watch(() => messages.value.length, async () => {
  await nextTick()
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
})

function send() {
  const t = text.value.trim()
  if (!t) return
  onSend(t)
  text.value = ''
}

function autoResize() {
  if (!textArea.value) return
  textArea.value.style.height = 'auto'
  textArea.value.style.height = Math.min(textArea.value.scrollHeight, 120) + 'px'
}

function getExpertEmoji(id?: string) {
  if (!id) return '🤖'
  return experts.value?.find(e => e.id === id)?.emoji || '🤖' || '🤖'
}

function getExpertColor(id?: string) {
  if (!id) return ''
  return colors[id] || ''
}

function getExpertTitle(id?: string) {
  if (!id) return ''
  return experts.value?.find(e => e.id === id)?.title || '' || ''
}

function quickSummon(id: string) {
  const expert = experts.value?.find(e => e.id === id)
  if (!expert) return
  triggerSummon(expert.id)
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return
  const file = input.files[0]
  uploadingFile.value = true
  uploadFileName.value = file.name
  try {
    // Step 1: 上传文件（立即返回 task_id）
    const formData = new FormData()
    formData.append('file', file)
    const uploadRes = await fetch('/api/upload', { method: 'POST', body: formData })
    const uploadData = await uploadRes.json()
    if (!uploadData.ok) {
      messages.value.push({ type: 'system', content: `文件上传失败：${uploadData.error || '未知错误'}`, timestamp: Date.now() })
      uploadingFile.value = false
      input.value = ''
      return
    }

    // Step 2: 轮询解析结果（最多 60s）
    const taskId = uploadData.task_id
    let parsedText = ''
    let truncated = false
    for (let i = 0; i < 60; i++) {
      await new Promise(r => setTimeout(r, 1000))
      try {
        const statusRes = await fetch(`/api/upload/status/${taskId}`)
        const statusData = await statusRes.json()
        if (statusData.status === 'done') {
          parsedText = statusData.parsed_text || ''
          truncated = statusData.truncated || false
          break
        }
        if (statusData.status === 'error') {
          messages.value.push({ type: 'system', content: `文件解析失败：${statusData.error || '未知错误'}`, timestamp: Date.now() })
          uploadingFile.value = false
          input.value = ''
          return
        }
      } catch {
        // 轮询网络抖动，继续重试
      }
    }

    if (parsedText) {
      const truncMsg = truncated ? '（内容已截断）' : ''
      const msg = `我上传了一个文件「${uploadData.filename}」${truncMsg}，内容如下：\n\n---\n${parsedText}\n---\n\n请分析此文件。`
      onSend(msg, true)
    } else {
      messages.value.push({ type: 'system', content: '文件解析超时，请稍后从档案馆重新解析。', timestamp: Date.now() })
    }
  } catch {
    messages.value.push({ type: 'system', content: '文件上传失败，请检查网络。', timestamp: Date.now() })
  }
  uploadingFile.value = false
  input.value = ''
}
</script>

<style scoped>
.session-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px var(--space-md);
  border-bottom: 1px solid var(--hairline);
  background: var(--surface-1);
  flex-shrink: 0;
}
.session-selector {
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}
.session-name {
  font-size: var(--text-caption);
  color: var(--ink-secondary);
}
.session-dropdown {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: calc(100% - var(--space-md) * 2);
  max-width: 400px;
  background: var(--surface-1);
  border: 1px solid var(--hairline-strong);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 100;
  max-height: 60vh;
  overflow-y: auto;
}
.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  font-size: var(--text-caption);
  cursor: pointer;
  border-bottom: 1px solid var(--hairline);
  gap: 8px;
}
.session-item:last-child { border-bottom: none; }
.session-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}
.session-date {
  font-size: var(--text-fine);
  color: var(--ink-muted);
}
.session-label { cursor: pointer; }
.rename-input {
  flex: 1;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  padding: 3px 6px;
  font-size: var(--text-caption);
  background: var(--surface-1);
  color: var(--ink);
  outline: none;
}
.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  cursor: pointer;
  font-size: 18px;
  color: var(--ink-muted);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
}
.upload-btn:hover { color: var(--accent); background: var(--hairline); }
.upload-toast {
  text-align: center;
  font-size: var(--text-fine);
  color: var(--accent);
  padding: 4px 0;
}
</style>
