<template>
  <div class="page">
    <div class="page-header">🎭 专家配置</div>
    <div style="display:flex;flex-direction:column;gap:var(--space-md);padding-bottom:calc(var(--space-3xl) + var(--safe-bottom));">

      <!-- 加载中 -->
      <div v-if="loading" class="text-center text-muted" style="padding:20px;">加载专家列表…</div>

      <!-- 专家列表：手风琴折叠 -->
      <div v-for="e in experts" :key="e.id" class="expert-accordion" :class="{ expanded: expandedId === e.id }">

        <!-- 折叠头部 -->
        <div class="accordion-header" @click="toggleExpert(e.id)">
          <div class="accordion-header-left">
            <span class="expert-emoji">{{ e.avatar }}</span>
            <div>
              <div class="expert-name">{{ e.name }}</div>
              <div class="expert-domain">{{ e.domain === 'all' ? '全域' : e.domain }}</div>
            </div>
          </div>
          <div class="accordion-header-right">
            <span v-if="!e.is_enabled" class="expert-disabled-badge">已停用</span>
            <span class="accordion-arrow">{{ expandedId === e.id ? '▾' : '▸' }}</span>
          </div>
        </div>

        <!-- 折叠内容 -->
        <div v-if="expandedId === e.id" class="accordion-body">

          <!-- 基本信息 -->
          <div class="edit-section">
            <h4>基本信息</h4>
            <div class="edit-row">
              <span class="edit-label">头像</span>
              <input v-model="e.avatar" class="edit-input" style="width:60px;text-align:center;" />
            </div>
            <div class="edit-row">
              <span class="edit-label">名称</span>
              <input v-model="e.name" class="edit-input" style="width:140px;" />
            </div>
            <div class="edit-row">
              <span class="edit-label">领域</span>
              <input v-model="e.domain" class="edit-input" style="width:140px;" />
            </div>
            <div class="edit-row">
              <span class="edit-label">启用</span>
              <button class="btn btn-ghost" style="height:30px;font-size:12px;padding:0 10px;" @click="e.is_enabled = !e.is_enabled">
                {{ e.is_enabled ? '✓ 已启用' : '✗ 已停用' }}
              </button>
            </div>
          </div>

          <!-- 召唤 -->
          <div class="edit-section">
            <h4>召唤仪式</h4>
            <div class="edit-row" style="flex-direction:column;align-items:stretch;gap:4px;">
              <span class="edit-label">召唤语</span>
              <input v-model="e.summon_phrase" class="edit-input" placeholder="用户输入此语召唤专家" />
            </div>
            <div class="edit-row" style="flex-direction:column;align-items:stretch;gap:4px;">
              <span class="edit-label">回应语</span>
              <input v-model="e.response_phrase" class="edit-input" placeholder="专家被召唤时的回应" />
            </div>
          </div>

          <!-- 人格设定 -->
          <div class="edit-section">
            <h4>人格设定</h4>
            <textarea
              v-model="e.system_prompt"
              class="edit-textarea"
              placeholder="编辑专家人格设定…"
            ></textarea>
          </div>

          <!-- 操作 -->
          <div style="display:flex;gap:8px;margin-top:12px;">
            <button class="btn btn-primary" style="flex:1;" @click="saveExpert(e)" :disabled="savingId === e.id">
              {{ savingId === e.id ? '保存中…' : '保存' }}
            </button>
            <button v-if="defaultExpertIds.includes(e.id)" class="btn btn-ghost" @click="resetExpert(e.id)">
              重置
            </button>
          </div>
          <div v-if="saveMsg && lastSavedId === e.id" :class="['save-msg', saveOk ? 'ok' : 'err']">{{ saveMsg }}</div>

        </div>
      </div>

      <!-- 新增专家 -->
      <div v-if="!showCreate" class="expert-accordion" style="cursor:pointer;" @click="showCreate = true">
        <div class="accordion-header" style="color:var(--accent);">
          <div class="accordion-header-left">
            <span class="expert-emoji">＋</span>
            <div class="expert-name">新增专家</div>
          </div>
          <div class="accordion-header-right">
            <span class="accordion-arrow">▸</span>
          </div>
        </div>
      </div>

      <!-- 新增专家表单 -->
      <div v-if="showCreate" class="expert-accordion expanded">
        <div class="accordion-header" @click="showCreate = false">
          <div class="accordion-header-left">
            <span class="expert-emoji">{{ newExpert.avatar || '🤖' }}</span>
            <div class="expert-name">{{ newExpert.name || '新专家' }}</div>
          </div>
          <div class="accordion-header-right">
            <span class="accordion-arrow">▾</span>
          </div>
        </div>
        <div class="accordion-body">
          <div class="edit-section">
            <h4>基本信息</h4>
            <div class="edit-row">
              <span class="edit-label">代号（英文ID）</span>
              <input v-model="newExpert.id" class="edit-input" style="width:180px;" placeholder="例如: guiguzi" />
            </div>
            <div class="edit-row">
              <span class="edit-label">名称</span>
              <input v-model="newExpert.name" class="edit-input" style="width:180px;" placeholder="例如: 鬼谷子" />
            </div>
            <div class="edit-row">
              <span class="edit-label">头像</span>
              <input v-model="newExpert.avatar" class="edit-input" style="width:60px;text-align:center;" placeholder="🤖" />
            </div>
            <div class="edit-row">
              <span class="edit-label">领域</span>
              <input v-model="newExpert.domain" class="edit-input" style="width:180px;" placeholder="例如: 策略" />
            </div>
          </div>
          <div class="edit-section">
            <h4>召唤仪式</h4>
            <div class="edit-row" style="flex-direction:column;align-items:stretch;gap:4px;">
              <span class="edit-label">召唤语</span>
              <input v-model="newExpert.summon_phrase" class="edit-input" placeholder="用户输入此语召唤专家" />
            </div>
            <div class="edit-row" style="flex-direction:column;align-items:stretch;gap:4px;">
              <span class="edit-label">回应语</span>
              <input v-model="newExpert.response_phrase" class="edit-input" placeholder="召唤时的回应" />
            </div>
          </div>
          <div class="edit-section">
            <h4>人格设定（可选，之后可编辑）</h4>
            <textarea v-model="newExpert.system_prompt" class="edit-textarea" placeholder="专家人格设定…"></textarea>
          </div>
          <div style="display:flex;gap:8px;margin-top:12px;">
            <button class="btn btn-primary" style="flex:1;" @click="doCreateExpert" :disabled="creating || !newExpert.id || !newExpert.name">
              {{ creating ? '创建中…' : '创建' }}
            </button>
            <button class="btn btn-ghost" @click="showCreate = false">取消</button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

interface Expert {
  id: string
  name: string
  avatar: string
  domain: string
  summon_phrase: string
  response_phrase: string
  system_prompt: string
  is_enabled: boolean
}

const experts = ref<Expert[]>([])
const loading = ref(true)
const expandedId = ref('')
const savingId = ref('')
const saveMsg = ref('')
const saveOk = ref(true)
const lastSavedId = ref('')
const showCreate = ref(false)
const creating = ref(false)

const defaultExpertIds = ['taishiling','zhongkui','chiyou','bigan','tanlang','zaojun','qibo','cangjie']

const newExpert = reactive({
  id: '', name: '', avatar: '🤖', domain: '',
  summon_phrase: '', response_phrase: '', system_prompt: '',
})

function toggleExpert(id: string) {
  expandedId.value = expandedId.value === id ? '' : id
}

async function fetchExperts() {
  loading.value = true
  try {
    const res = await fetch('/api/experts')
    if (res.ok) {
      const list = await res.json()
      // 为每个专家拉取完整人格文件
      for (const e of list) {
        try {
          const detailRes = await fetch(`/api/experts/${e.id}`)
          if (detailRes.ok) {
            const detail = await detailRes.json()
            e.system_prompt = detail.system_prompt || ''
          }
        } catch { /* use empty prompt */ }
        if (!e.system_prompt) e.system_prompt = ''
      }
      experts.value = list
    }
  } catch { /* use defaults */ }
  loading.value = false
}

async function saveExpert(e: Expert) {
  savingId.value = e.id
  try {
    const res = await fetch(`/api/experts/${e.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(e),
    })
    if (res.ok) {
      saveOk.value = true
      saveMsg.value = `✓ ${e.name} 已保存`
    } else {
      saveOk.value = false
      saveMsg.value = '保存失败'
    }
  } catch {
    saveOk.value = false
    saveMsg.value = '保存失败，请检查网络'
  }
  lastSavedId.value = e.id
  savingId.value = ''
  setTimeout(() => { saveMsg.value = '' }, 2000)
}

async function resetExpert(id: string) {
  if (!window.confirm('确定重置此专家到默认值？')) return
  try {
    const res = await fetch(`/api/experts/${id}/reset`, { method: 'POST' })
    if (res.ok) await fetchExperts()
  } catch { /* ignore */ }
}

async function doCreateExpert() {
  if (!newExpert.id || !newExpert.name) return
  creating.value = true
  try {
    const res = await fetch('/api/experts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newExpert }),
    })
    if (res.ok) {
      showCreate.value = false
      Object.assign(newExpert, { id:'', name:'', avatar:'🤖', domain:'', summon_phrase:'', response_phrase:'', system_prompt:'' })
      await fetchExperts()
    } else {
      alert('创建失败，请检查ID是否重复')
    }
  } catch { alert('创建失败，请检查网络') }
  creating.value = false
}

onMounted(fetchExperts)
</script>

<style scoped>
.expert-accordion {
  border: 1px solid var(--hairline);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-1);
}
.accordion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}
.accordion-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.accordion-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.expert-emoji {
  font-size: 1.5rem;
  width: 36px;
  text-align: center;
}
.expert-name {
  font-weight: 600;
  font-size: var(--text-body);
}
.expert-domain {
  font-size: var(--text-caption);
  color: var(--ink-muted);
  margin-top: 2px;
}
.expert-disabled-badge {
  font-size: 11px;
  color: var(--ink-muted);
  background: var(--hairline);
  padding: 2px 6px;
  border-radius: 4px;
}
.accordion-arrow {
  font-size: 14px;
  color: var(--ink-muted);
}

.accordion-body {
  padding: 0 16px 16px;
  border-top: 1px solid var(--hairline);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-section h4 {
  font-size: var(--text-caption);
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 12px 0 6px;
}

.edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.edit-label {
  font-size: var(--text-caption);
  color: var(--ink-muted);
  min-width: 56px;
}
.edit-input {
  border: 1px solid var(--hairline-strong);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  font-size: var(--text-caption);
  background: var(--surface-1);
  color: var(--ink);
}
.edit-input:focus {
  outline: none;
  border-color: var(--accent);
}
.edit-textarea {
  width: 100%;
  min-height: 180px;
  border: 1px solid var(--hairline-strong);
  border-radius: var(--radius-sm);
  padding: 10px;
  font-family: var(--font-text);
  font-size: var(--text-caption);
  line-height: 1.5;
  resize: vertical;
  background: var(--surface-1);
  color: var(--ink);
}
.edit-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.save-msg {
  font-size: var(--text-caption);
  margin-top: 4px;
}
.save-msg.ok { color: var(--accent); }
.save-msg.err { color: var(--danger); }
</style>
