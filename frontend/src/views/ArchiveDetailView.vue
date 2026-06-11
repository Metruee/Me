<template>
  <div class="page">
    <div class="page-title">📄 档案详情</div>
    <div v-if="loading" class="empty-state">
      <div class="empty-state-text">加载中…</div>
    </div>
    <div v-else-if="!entry" class="empty-state">
      <div class="empty-state-icon">📭</div>
      <div class="empty-state-text">未找到该档案条目</div>
    </div>
    <div v-else class="detail-card">
      <!-- 显示模式 -->
      <template v-if="!editing">
        <div class="detail-meta">
          <span class="detail-tag">{{ entry.theme_main }}</span>
          <div style="display:flex;align-items:center;gap:12px;">
            <span class="detail-date">{{ entry.created_at }}</span>
            <button class="btn btn-ghost" style="height:28px;font-size:11px;padding:0 10px;" @click="startEdit">✎ 编辑</button>
            <button class="btn btn-ghost" style="height:28px;font-size:11px;padding:0 10px;color:var(--danger);" @click="doDelete">✕ 删除</button>
          </div>
        </div>
        <div class="detail-section">
          <h4>摘要</h4>
          <p>{{ entry.summary }}</p>
        </div>
        <div v-if="entry.original_text" class="detail-section">
          <h4>原文</h4>
          <p class="detail-original">{{ entry.original_text }}</p>
        </div>
        <div v-if="entry.expert_id" class="detail-section">
          <h4>来源专家</h4>
          <p>{{ entry.expert_id }}</p>
        </div>
      </template>

      <!-- 编辑模式 -->
      <template v-else>
        <div class="edit-section">
          <h4>归属主题</h4>
          <input v-model="editForm.theme_main" class="edit-input" />
        </div>
        <div class="edit-section">
          <h4>摘要</h4>
          <textarea v-model="editForm.summary" class="edit-textarea" rows="3"></textarea>
        </div>
        <div class="edit-section">
          <h4>原文</h4>
          <textarea v-model="editForm.original_text" class="edit-textarea" rows="5"></textarea>
        </div>
        <div style="display:flex;gap:8px;margin-top:var(--space-md);">
          <button class="btn btn-primary" @click="doSave" :disabled="saving">保存</button>
          <button class="btn btn-ghost" @click="cancelEdit">取消</button>
        </div>
        <div v-if="saveMsg" class="save-msg">{{ saveMsg }}</div>
      </template>

      <button class="btn btn-ghost" style="margin-top:var(--space-lg);" @click="$router.back()">← 返回列表</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const entry = ref<any>(null)
const editing = ref(false)
const saving = ref(false)
const saveMsg = ref('')

const editForm = reactive({ theme_main: '', summary: '', original_text: '' })

function startEdit() {
  editForm.theme_main = entry.value.theme_main || ''
  editForm.summary = entry.value.summary || ''
  editForm.original_text = entry.value.original_text || ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  saveMsg.value = ''
}

async function doSave() {
  saving.value = true
  try {
    const res = await fetch(`/api/knowledge/entries/${route.params.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editForm),
    })
    if (res.ok) {
      entry.value.theme_main = editForm.theme_main
      entry.value.summary = editForm.summary
      entry.value.original_text = editForm.original_text
      editing.value = false
      saveMsg.value = ''
    } else {
      saveMsg.value = '保存失败'
    }
  } catch {
    saveMsg.value = '保存失败，请检查网络'
  }
  saving.value = false
}

async function doDelete() {
  if (!window.confirm('确定删除此档案条目？')) return
  try {
    await fetch(`/api/knowledge/entries/${route.params.id}`, { method: 'DELETE' })
    router.push('/archive')
  } catch { alert('删除失败') }
}

onMounted(async () => {
  try {
    const res = await fetch(`/api/knowledge/entries/${route.params.id}`)
    if (res.ok) entry.value = await res.json()
  } catch { /* not found */ }
  loading.value = false
})
</script>

<style scoped>
.detail-card { background: var(--surface-1); border: 1px solid var(--hairline); border-radius: var(--radius-md); padding: var(--space-lg); }
.detail-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-lg); }
.detail-tag { font-size: var(--text-caption); background: var(--accent-soft); color: var(--accent); padding: 2px 10px; border-radius: var(--radius-pill); }
.detail-date { font-size: var(--text-caption); color: var(--ink-muted); }
.detail-section { margin-bottom: var(--space-md); }
.detail-section h4 { font-size: var(--text-caption); color: var(--ink-muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.detail-section p { font-size: var(--text-body); line-height: 1.6; }
.detail-original { white-space: pre-wrap; color: var(--ink-secondary); }
.edit-section { margin-bottom: var(--space-md); }
.edit-section h4 { font-size: var(--text-caption); color: var(--ink-muted); margin-bottom: 4px; }
.edit-input { width: 100%; border: 1px solid var(--hairline-strong); border-radius: var(--radius-sm); padding: 8px; font-size: var(--text-body); background: var(--surface-1); color: var(--ink); }
.edit-textarea { width: 100%; border: 1px solid var(--hairline-strong); border-radius: var(--radius-sm); padding: 8px; font-size: var(--text-body); resize: vertical; background: var(--surface-1); color: var(--ink); }
.save-msg { font-size: var(--text-caption); color: var(--danger); margin-top: 4px; }
</style>
