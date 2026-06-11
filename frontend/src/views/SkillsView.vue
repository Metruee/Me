<template>
  <div class="page">
    <div class="page-header">🔧 技能管理</div>
    <div style="display:flex;flex-direction:column;gap:var(--space-md);padding-bottom:calc(var(--space-3xl) + var(--safe-bottom));">

      <!-- 加载中 -->
      <div v-if="loading" class="text-center text-muted" style="padding:20px;">加载技能列表…</div>

      <!-- 技能列表 -->
      <div v-if="!loading && skills.length" class="skills-list">
        <div v-for="s in skills" :key="s.id" class="skill-card">
          <div class="skill-info">
            <div class="skill-name">{{ s.name }}</div>
            <div class="skill-desc">{{ s.description || (s.has_manifest ? '📄 已配置 SKILL.md' : '⚠️ 缺少清单文件') }}</div>
          </div>
          <button
            class="btn btn-ghost"
            style="height:30px;font-size:12px;padding:0 10px;margin-right:8px;"
            @click="toggleSkill(s)"
            :disabled="togglingId === s.id"
          >
            {{ togglingId === s.id ? '…' : (s.enabled ? '✓ 已启用' : '✗ 已停用') }}
          </button>
          <button
            class="btn btn-ghost"
            style="height:30px;font-size:11px;padding:0 6px;flex-shrink:0;color:var(--ink-muted)"
            @click.stop="removeSkill(s)"
            :disabled="deletingId === s.id"
          >
            {{ deletingId === s.id ? '…' : '🗑' }}
          </button>
        </div>
      </div>

      <!-- 上传技能包 -->
      <div class="upload-zone" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
        <span>{{ uploading ? '正在导入…' : '📦 点击或拖拽 .zip 文件上传技能包' }}</span>
        <input ref="fileInput" type="file" accept=".zip" style="display:none" @change="onFileChange" />
      </div>
      <div v-if="uploadMsg" class="gen-msg">{{ uploadMsg }}</div>

      <!-- 空态 -->
      <div v-if="!loading && skills.length === 0" class="text-center text-muted" style="padding:20px;">
        暂无技能。将技能文件夹放入 /app/skills 即可自动发现。
      </div>

      <div class="text-fine" style="color:var(--ink-muted);margin-top:4px;font-size:11px;">
        技能目录：/app/skills &nbsp;|&nbsp; 文件工具：已启用
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Skill {
  id: string
  name: string
  has_manifest: boolean
  description: string
  enabled: boolean
}

const skills = ref<Skill[]>([])
const loading = ref(true)
const togglingId = ref('')
const deletingId = ref('')
const uploading = ref(false)
const uploadMsg = ref('')
const fileInput = ref<HTMLInputElement>()

async function fetchSkills() {
  loading.value = true
  try {
    const res = await fetch('/api/skills')
    if (res.ok) skills.value = await res.json()
  } catch { /* use empty list */ }
  loading.value = false
}

async function toggleSkill(s: Skill) {
  togglingId.value = s.id
  const newEnabled = !s.enabled
  try {
    const res = await fetch(`/api/skills/${s.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: newEnabled }),
    })
    if (res.ok) s.enabled = newEnabled
  } catch { /* ignore */ }
  togglingId.value = ''
}

onMounted(fetchSkills)

function triggerUpload() {
  fileInput.value?.click()
}

async function uploadFile(file: File) {
  uploading.value = true
  uploadMsg.value = ''
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch('/api/skills/upload', { method: 'POST', body: form })
    const data = await res.json()
    if (data.ok) {
      uploadMsg.value = `导入成功：${data.imported} 个技能 (${data.skills?.join(', ')})`
      await fetchSkills()
    } else {
      uploadMsg.value = data.detail || '导入失败'
    }
  } catch {
    uploadMsg.value = '上传失败，请检查网络'
  }
  uploading.value = false
}

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) uploadFile(file)
}

function onDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadFile(file)
}

async function removeSkill(s: Skill) {
  if (!confirm(`确定删除技能「${s.name}」？\n\n⚠️ 此操作将从系统中永久移除该技能及其所有文件。\n后续若需继续使用，需要重新上传。`)) return
  deletingId.value = s.id
  try {
    const res = await fetch(`/api/skills/${s.id}`, { method: 'DELETE' })
    if (res.ok) {
      skills.value = skills.value.filter(sk => sk.id !== s.id)
    }
  } catch { /* ignore */ }
  deletingId.value = ''
}
</script>

<style scoped>
.gen-msg {
  background: var(--hairline);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: 12px;
  color: var(--ink-muted);
}
.upload-zone {
  border: 2px dashed var(--hairline);
  border-radius: var(--radius-md);
  padding: 20px;
  text-align: center;
  font-size: 13px;
  color: var(--ink-muted);
  cursor: pointer;
  transition: border-color .2s;
}
.upload-zone:hover { border-color: var(--amber); color: var(--amber-light); }
</style>
